from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import RoleEnum

# Configuração de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Constantes JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar se a senha em texto puro bate com o hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gerar hash da senha"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Criar token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verificar e decodificar token JWT"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return payload
    except JWTError:
        return None


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Buscar usuário por email"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Autenticar usuário com email e senha"""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.ativo:
        return None
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency para obter usuário atual do token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = await get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency para usuário ativo (redundante, mas clara)"""
    return current_user


def require_role(required_role: RoleEnum):
    """Factory para criar dependency que exige role específica"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_hierarchy = {
            RoleEnum.FUNCIONARIO: 1,
            RoleEnum.GESTOR: 2,
            RoleEnum.DIRETOR: 3
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer nível: {required_role.value}"
            )
        return current_user
    
    return role_checker


def require_gestor_or_above():
    """Dependency que exige Gestor ou Diretor"""
    return require_role(RoleEnum.GESTOR)


def require_diretor():
    """Dependency que exige Diretor"""
    return require_role(RoleEnum.DIRETOR)


def can_access_setor(user: User, setor: str) -> bool:
    """Verificar se usuário pode acessar dados do setor"""
    # Diretor acessa tudo
    if user.role == RoleEnum.DIRETOR:
        return True
    
    # Gestor acessa tudo também (assumindo que há gestores multi-setor)
    if user.role == RoleEnum.GESTOR:
        return True
    
    # Funcionário só acessa seu próprio setor
    if user.role == RoleEnum.FUNCIONARIO:
        return user.setor == setor
    
    return False


class SetorAccessChecker:
    """Classe para verificar acesso a setores específicos"""
    
    def __init__(self, setor: str):
        self.setor = setor
    
    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not can_access_setor(current_user, self.setor):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado ao setor: {self.setor}"
            )
        return current_user


# Helpers para setores específicos
def require_marketing_access():
    return SetorAccessChecker("Marketing")

def require_comercial_access():
    return SetorAccessChecker("Comercial")

def require_eventos_access():
    return SetorAccessChecker("Eventos")

def require_rh_access():
    return SetorAccessChecker("RH")

def require_pedagogico_access():
    return SetorAccessChecker("Pedagógico")

def require_financeiro_access():
    return SetorAccessChecker("Financeiro")


# Schemas para autenticação
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # em segundos
    user: dict


class TokenData(BaseModel):
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str