from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import ERR_VALIDATION, BusinessException
from app.schemas.response import fail

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="慧编学伴——智能编程学习助教系统 API",
        version="0.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(BusinessException)
    async def business_exception_handler(_: Request, exc: BusinessException):
        return JSONResponse(status_code=200, content=fail(exc.code, exc.message, exc.data))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=200,
            content=fail(ERR_VALIDATION, "参数校验失败", exc.errors()),
        )

    @app.get("/health")
    async def health_check():
        return {
            "code": 0,
            "message": "ok",
            "data": {
                "status": "healthy",
                "app": settings.app_name,
                "env": settings.app_env,
            },
        }

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
