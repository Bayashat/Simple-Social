from app.schemas import UserRead, UserUpdate
from app.users import fastapi_users

router = fastapi_users.get_users_router(UserRead, UserUpdate)
