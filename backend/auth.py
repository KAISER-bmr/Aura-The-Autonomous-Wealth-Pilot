"""
backend/auth.py
Aura — Lightweight JWT Authentication
Protects API endpoints. Uses python-jose + passlib.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# ─── CONFIG ───────────────────────────────────────────────────────────────────

SECRET_KEY  = os.getenv("AURA_SECRET_KEY", "aura-3g2b-orchestron-secret-2025")
ALGORITHM   = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 8   # 8-hour sessions

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ─── MOCK USER STORE ──────────────────────────────────────────────────────────
# In production, replace with a real DB table

MOCK_USERS = {
    "priya": {
        "username":      "priya",
        "full_name":     "Priya Sharma",
        "hashed_password": pwd_context.hash("aura2025"),
        "user_id":       "usr_001",
        "disabled":      False
    },
    "demo": {
        "username":      "demo",
        "full_name":     "Demo User",
        "hashed_password": pwd_context.hash("demo"),
        "user_id":       "usr_demo",
        "disabled":      False
    }
}


# ─── MODELS ───────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type:   str
    user_id:      str
    full_name:    str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username:  str
    full_name: str
    user_id:   str
    disabled:  bool


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_user(username: str) -> Optional[dict]:
    return MOCK_USERS.get(username)

def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire    = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = get_user(username)
    if user is None:
        raise cred_exc
    return User(**{k: user[k] for k in ["username","full_name","user_id","disabled"]})

async def get_active_user(current: User = Depends(get_current_user)) -> User:
    if current.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current


# ─── AUTH ROUTER (mount in api.py) ────────────────────────────────────────────

from fastapi import APIRouter
auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/token", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    )
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user["user_id"],
        full_name=user["full_name"]
    )

@auth_router.get("/me", response_model=User)
async def read_me(current: User = Depends(get_active_user)):
    return current
