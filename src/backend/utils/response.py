from typing import Any, Optional
from fastapi.responses import JSONResponse


def success(data: Any = None, msg: str = "成功", code: int = 0, status_code: int = 200) -> JSONResponse:
    payload = {"code": code, "msg": msg, "data": data}
    return JSONResponse(content=payload, status_code=status_code)


def error(msg: str = "错误", code: int = 400, data: Optional[Any] = None, status_code: Optional[int] = None) -> JSONResponse:
    sc = status_code if status_code is not None else (code if 100 <= code < 600 else 400)
    payload = {"code": code, "msg": msg, "data": data}
    return JSONResponse(content=payload, status_code=sc)
