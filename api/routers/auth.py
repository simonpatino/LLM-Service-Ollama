from datetime import timedelta

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from api.core.database import engine
from api.core.security import hash_password, verify_password, create_access_token
from api.models.user import Users, UserCreate, UserLogin, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=Users)
def create_user(user_data: UserCreate) -> dict:
    """Register a new user."""
    with Session(engine) as session:
        existing_user = session.exec(
            select(Users).where(Users.username == user_data.username)
        ).first()

        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        hashed_pw = hash_password(user_data.password)
        user = Users(username=user_data.username, hashed_password=hashed_pw)
        session.add(user)
        session.commit()
        session.refresh(user)

        return {"id": user.id, "username": user.username}


@router.post("/login", response_model=TokenResponse)
def login_user(login_data: UserLogin) -> TokenResponse:
    """Login and get an access token."""
    with Session(engine) as session:
        user = session.exec(
            select(Users).where(Users.username == login_data.username)
        ).first()

        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=timedelta(hours=1)
        )

        return TokenResponse(access_token=access_token)
