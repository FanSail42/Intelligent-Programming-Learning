from fastapi import APIRouter

from app.api.v1 import admin_ai, admin_users, auth, chat, code, courses, learning, materials, teacher, warehouses

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(courses.router)
api_router.include_router(materials.router)
api_router.include_router(warehouses.router)
api_router.include_router(chat.router)
api_router.include_router(code.router)
api_router.include_router(learning.router)
api_router.include_router(teacher.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_ai.router)
