from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(data, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "data": jsonable_encoder(data, by_alias=True)},
    )


def error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"success": False, "error": message})
