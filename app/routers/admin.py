from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_active_admin
from app.models.user import User

router = APIRouter(tags=["Admin"])

@router.get("/dashboard")
def admin_dashboard(admin: User = Depends(get_current_active_admin)):
    return {
        "message": "Welcome Admin 👑",
        "admin": admin.username,
        "role": admin.role
    }

@router.get("/users", tags=["Admin - Users"])
def list_all_users(admin: User = Depends(get_current_active_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role
        }
        for u in users
    ]


@router.delete("/users/{user_id}", tags=["Admin - Users"])
def delete_user(
        user_id: int,
        admin: User = Depends(get_current_active_admin),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "ADMIN":
        raise HTTPException(status_code=403, detail="Cannot delete admin user")

    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} deleted successfully"}
