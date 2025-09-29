# backend/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.services.auth_service import AuthService, get_auth_service
from app.schemas import UserCreate, UserResponse, RoleEnum
from app.auth import get_current_user
from app.models import User

# Schema para login (criado localmente para não modificar schemas.py)
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Configurar router
router = APIRouter(
    prefix="/auth",
    tags=["autenticação"]
)

# Configurar segurança
security = HTTPBearer()


@router.post("/register", response_model=Dict[str, Any])
async def register_user(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registra um novo usuário no sistema
    
    - **email**: Email único do usuário
    - **nome**: Nome completo
    - **password**: Senha (mínimo 6 caracteres)
    - **role**: Papel do usuário (Funcionário, Gestor, Diretor)
    - **setor**: Setor de trabalho
    """
    auth_service = get_auth_service(db)
    
    try:
        result = auth_service.create_user(user_create)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post("/login", response_model=Dict[str, Any])
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Realiza login no sistema
    
    - **email**: Email do usuário
    - **password**: Senha do usuário
    
    Retorna token de acesso JWT válido por 30 minutos
    """
    auth_service = get_auth_service(db)
    
    try:
        result = auth_service.login(login_data.email, login_data.password)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Retorna informações do usuário atual autenticado
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        nome=current_user.nome,
        role=current_user.role,
        setor=current_user.setor,
        cargo=current_user.cargo,
        ativo=current_user.ativo,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout do usuário (invalida token no lado cliente)
    
    Nota: JWT tokens são stateless, então o logout é feito 
    invalidando o token no lado cliente. Em produção, 
    considere usar uma blacklist de tokens.
    """
    return {
        "status": "success",
        "message": "Logout realizado com sucesso",
        "instructions": "Remova o token do armazenamento local do cliente"
    }


@router.post("/create-admin", response_model=Dict[str, Any])
async def create_admin_user(
    db: Session = Depends(get_db)
):
    """
    Cria usuário administrador padrão
    
    ⚠️ ATENÇÃO: Esta rota é para setup inicial apenas.
    Em produção, remova ou proteja esta rota.
    
    Credenciais padrão:
    - Email: admin@kpidashboard.com
    - Senha: admin123
    """
    auth_service = get_auth_service(db)
    
    try:
        result = auth_service.create_admin_user()
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get("/users", response_model=Dict[str, Any])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista usuários do sistema
    
    Permissões:
    - DIRETOR: vê todos os usuários
    - GESTOR: vê usuários do mesmo setor
    - FUNCIONARIO: sem acesso
    """
    auth_service = get_auth_service(db)
    
    try:
        result = auth_service.list_users(current_user, limit=limit, offset=offset)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.patch("/users/{user_id}/deactivate", response_model=Dict[str, Any])
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Desativa um usuário (soft delete)
    
    Apenas diretores podem desativar usuários.
    Não é possível desativar o próprio usuário.
    """
    auth_service = get_auth_service(db)
    
    try:
        result = auth_service.deactivate_user(user_id, current_user)
        return result
    except ValueError as e:
        if "Permissão negada" in str(e) or "Apenas diretores" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get("/check-permissions")
async def check_user_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifica as permissões do usuário atual
    """
    auth_service = get_auth_service(db)
    
    permissions = {
        "user_info": {
            "id": current_user.id,
            "email": current_user.email,
            "nome": current_user.nome,
            "role": current_user.role,
            "setor": current_user.setor
        },
        "can_manage_users": auth_service.check_permission(current_user, RoleEnum.GESTOR),
        "can_deactivate_users": auth_service.check_permission(current_user, RoleEnum.DIRETOR),
        "accessible_setores": {
            "marketing": auth_service.can_access_setor(current_user, "marketing"),
            "comercial": auth_service.can_access_setor(current_user, "comercial"),
            "eventos": auth_service.can_access_setor(current_user, "eventos"),
            "rh": auth_service.can_access_setor(current_user, "rh"),
            "pedagogico": auth_service.can_access_setor(current_user, "pedagogico"),
            "financeiro": auth_service.can_access_setor(current_user, "financeiro")
        }
    }
    
    return {
        "status": "success",
        "permissions": permissions
    }


@router.get("/health")
async def auth_health_check():
    """
    Health check para o sistema de autenticação
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "available_roles": [role.value for role in RoleEnum],
        "endpoints": [
            "POST /auth/register",
            "POST /auth/login", 
            "GET /auth/me",
            "POST /auth/logout",
            "POST /auth/create-admin",
            "GET /auth/users",
            "PATCH /auth/users/{id}/deactivate",
            "GET /auth/check-permissions"
        ]
    }