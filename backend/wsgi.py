# wsgi.py — WSGI wrapper for shared hosting panels (Passenger/mod_wsgi)
# Converts FastAPI (ASGI) to WSGI callable expected by the hosting panel
from a2wsgi import ASGIMiddleware
from main import app

application = ASGIMiddleware(app)
