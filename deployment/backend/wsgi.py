# wsgi.py — ASGI-to-WSGI bridge for Passenger (no threads, shared hosting)
import asyncio
import sys
from http import HTTPStatus

# ── Persistent event loop (same loop = aiomysql pool stays alive) ──
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

from main import app  # noqa: E402

# ── Fire lifespan.startup so @app.on_event("startup") runs ────────
async def _trigger_startup():
    _started = False
    _done = asyncio.Event()

    async def receive():
        nonlocal _started
        if not _started:
            _started = True
            return {"type": "lifespan.startup"}
        await asyncio.sleep(86400 * 365)
        return {"type": "lifespan.shutdown"}

    async def send(msg):
        if msg["type"] in ("lifespan.startup.complete", "lifespan.startup.failed"):
            _done.set()

    asyncio.ensure_future(
        app({"type": "lifespan", "asgi": {"version": "3.0"}}, receive, send)
    )
    await asyncio.wait_for(_done.wait(), timeout=30)

# Lifespan startup disabled — LiteSpeed forks workers from parent,
# DB connections created here would be shared/corrupted across children.
# With NullPool each request gets its own fresh connection.
# try:
#     _loop.run_until_complete(_trigger_startup())
# except Exception as e:
#     print(f"[wsgi] WARNING: startup failed: {e}", file=sys.stderr)


# ── WSGI callable ─────────────────────────────────────────────────
def application(environ, start_response):
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": environ["REQUEST_METHOD"],
        "path": environ.get("PATH_INFO", "/"),
        "query_string": environ.get("QUERY_STRING", "").encode("latin-1"),
        "root_path": environ.get("SCRIPT_NAME", ""),
        "scheme": environ.get("wsgi.url_scheme", "http"),
        "server": (environ["SERVER_NAME"], int(environ.get("SERVER_PORT", "80"))),
        "headers": _extract_headers(environ),
    }
    body = _read_body(environ)

    try:
        status_line, resp_headers, resp_body = _loop.run_until_complete(
            _asgi_handle(scope, body)
        )
    except Exception as exc:
        print(f"[wsgi] ERROR: {exc}", file=sys.stderr)
        start_response("500 Internal Server Error",
                        [("Content-Type", "text/plain")])
        return [b"Internal Server Error"]

    start_response(status_line, resp_headers)
    return [resp_body]


# ── helpers ────────────────────────────────────────────────────────
def _extract_headers(environ):
    headers = []
    for key, val in environ.items():
        if key.startswith("HTTP_"):
            name = key[5:].lower().replace("_", "-")
            headers.append((name.encode("latin-1"), val.encode("latin-1")))
    ct = environ.get("CONTENT_TYPE")
    if ct:
        headers.append((b"content-type", ct.encode("latin-1")))
    cl = environ.get("CONTENT_LENGTH")
    if cl:
        headers.append((b"content-length", cl.encode("latin-1")))
    return headers


def _read_body(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH", 0))
    except (ValueError, TypeError):
        length = 0
    return environ["wsgi.input"].read(length) if length else b""


async def _asgi_handle(scope, body):
    status_line = "500 Internal Server Error"
    resp_headers = []
    resp_body = bytearray()

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(msg):
        nonlocal status_line, resp_headers
        if msg["type"] == "http.response.start":
            code = msg["status"]
            try:
                phrase = HTTPStatus(code).phrase
            except ValueError:
                phrase = ""
            status_line = f"{code} {phrase}"
            resp_headers = [
                (k.decode("latin-1"), v.decode("latin-1"))
                for k, v in msg.get("headers", [])
            ]
        elif msg["type"] == "http.response.body":
            resp_body.extend(msg.get("body", b""))

    await app(scope, receive, send)
    return status_line, resp_headers, bytes(resp_body)
