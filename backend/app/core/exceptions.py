from typing import Any


class BusinessException(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


# Error codes (see docs/api-convention.md)
ERR_VALIDATION = 40001
ERR_MATERIAL_DUPLICATE = 40002
ERR_UNAUTHORIZED = 40101
ERR_FORBIDDEN = 40301
ERR_NOT_FOUND = 40401
ERR_RATE_LIMIT = 42901
ERR_INTERNAL = 50001
