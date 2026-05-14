# app/routers/usersprotected.py
from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.security import get_current_user, oauth2_scheme

router = APIRouter()


@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role
    }


@router.get("/test-auth")
def test_auth(token: str = Depends(oauth2_scheme)):
    return {"token": token, "message": "Token is valid ✅"}

