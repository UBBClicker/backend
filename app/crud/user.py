from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def register(self, db: Session, user: UserCreate) -> User:
        """Register a new user with hashed password."""
        hashed_password = get_password_hash(user.password)
        # Create the model directly instead of passing through UserCreate again
        db_obj = User(nickname=user.nickname, password=hashed_password)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_nickname(self, db: Session, nickname: str) -> User:
        """Get a user by nickname."""
        return self.get_by_attribute(db, "nickname", nickname)
    
    def authenticate(self, db: Session, nickname: str, password: str) -> User | None:
        """Authenticate a user with nickname and password."""
        user = self.get_by_nickname(db, nickname)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user


user = CRUDUser(User)