from typing import Any


def ok(data: Any = None, msg: str = "") -> dict:
    return {"code": 200, "msg": msg, "data": data}


def err(code: int, msg: str) -> dict:
    return {"code": code, "msg": msg, "data": None}
