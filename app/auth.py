from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User


def get_current_user(x_user_id: int = Header(...), db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.id == x_user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user context. Pass x-user-id header.")
    return user


def require_roles(*allowed: Role):
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Forbidden for your role")
        return user

    return _checker


def require_same_company_or_admin(resource_company_id: int, user: User):
    if user.role == Role.PLATFORM_ADMIN:
        return
    if user.company_id != resource_company_id:
        raise HTTPException(status_code=403, detail="Resource belongs to another company")
