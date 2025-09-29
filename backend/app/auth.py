from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import RoleEnum

# Configuração de segurança
security = HTTPBearer()

# Constantes JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar se a senha em texto puro bate com o hash usando bcrypt direto"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Gerar hash da senha usando bcrypt direto"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Criar token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    # CORREÇÃO: usar settings.SECRET_KEY (não JWT_SECRET)
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verificar e decodificar token JWT"""
    try:
        # CORREÇÃO: usar settings.SECRET_KEY (não JWT_SECRET)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return payload
    except JWTError:
        return None


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Buscar usuário por email - VERSÃO SÍNCRONA"""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Autenticar usuário com email e senha - VERSÃO SÍNCRONA"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.ativo:
        return None
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency para obter usuário atual do token JWT - VERSÃO SÍNCRONA"""
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
    
    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency para usuário ativo (redundante, mas clara)"""
    return current_user


def require_role(required_role: RoleEnum):
    """Factory para criar dependency que exige role específica"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_hierarchy = {
            RoleEnum.FUNCIONARIO: 1,
            RoleEnum.GESTOR: 2,
            RoleEnum.DIRETOR: 3
        }
        
        try:
            user_role = RoleEnum(current_user.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role do usuário inválida"
            )
        
        user_level = role_hierarchy.get(user_role, 0)
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
    try:
        user_role = RoleEnum(user.role)
    except ValueError:
        return False
    
    # Diretor acessa tudo
    if user_role == RoleEnum.DIRETOR:
        return True
    
    # Gestor acessa tudo também (assumindo que há gestores multi-setor)
    if user_role == RoleEnum.GESTOR:
        return True
    
    # Funcionário só acessa seu próprio setor
    if user_role == RoleEnum.FUNCIONARIO:
        return user.setor and user.setor.lower() == setor.lower()
    
    return False


class SetorAccessChecker:
    """Classe para verificar acesso a setores específicos"""
    
    def __init__(self, setor: str):
        self.setor = setor
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
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