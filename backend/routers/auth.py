"""
Router de Autenticação — POST /api/auth/login, GET /api/auth/me
Compatível com a tabela `users` existente (senha em texto plano).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import os
import jwt   # PyJWT

from ..database import get_db
from .. import models

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET_KEY  = os.getenv("JWT_SECRET", "sga-h-super-secret-key-change-in-prod-2026")
ALGORITHM   = "HS256"
TOKEN_HOURS = 24 * 7   # 7 dias

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=TOKEN_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


def user_to_dict(u: models.User) -> dict:
    return {
        "id":        str(u.id),
        "username":  u.username,
        "full_name": u.full_name,
        "email":     u.email,
        "role":      u.role or "teacher",
        "is_active": u.is_active if u.is_active is not None else True,
    }


# ─────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────

@router.post("/login")
def login(payload: dict, db: Session = Depends(get_db)):
    """
    Aceita { "username": "...", "password": "..." }
    Compara com a tabela users (senha em texto plano — compatível com legado).
    Retorna { "access_token": "...", "token_type": "bearer", "user": {...} }
    """
    username: str = payload.get("username", "").strip()
    password: str = payload.get("password", "")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="username e password são obrigatórios."
        )

    # Buscar usuário
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Verificar senha — suporte a texto plano (legado) e bcrypt (futuro)
    password_ok = False
    stored = user.password or ""

    if stored.startswith("$2b$") or stored.startswith("$2a$"):
        # bcrypt hash — usar passlib se disponível
        try:
            from passlib.context import CryptContext
            pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
            password_ok = pwd_ctx.verify(password, stored)
        except ImportError:
            password_ok = False
    else:
        # Texto plano (banco legado)
        password_ok = (password == stored)

    if not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Contate o administrador."
        )

    user_data = user_to_dict(user)
    token = create_token({"sub": str(user.id), **user_data})

    return {
        "access_token": token,
        "token_type":   "bearer",
        "user":         user_data,
    }


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    user_id = payload.get("sub")
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido.")

    user = db.query(models.User).filter(models.User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    if user.is_active is False:
        raise HTTPException(status_code=403, detail="Usuário inativo.")

    return user

@router.get("/me")
def get_me(user: models.User = Depends(get_current_user)):
    """Retorna o usuário autenticado a partir do Bearer token."""
    return user_to_dict(user)
