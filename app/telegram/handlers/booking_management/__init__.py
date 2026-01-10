from .create import router as create_router
from .view import router as view_router
from .edit import router as edit_router

booking_routers = [create_router, view_router, edit_router]
