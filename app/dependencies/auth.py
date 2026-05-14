# app/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from app.models.user import User, UserRole
from app.core.security import get_current_user

def get_current_active_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user
