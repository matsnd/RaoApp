from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def not_found(resource: str = "Zasób") -> HTTPException:
    return HTTPException(status_code=404, detail=f"{resource} nie znaleziony")


def conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=409, detail=detail)


def bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


def forbidden(detail: str = "Brak uprawnień") -> HTTPException:
    return HTTPException(status_code=403, detail=detail)


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
