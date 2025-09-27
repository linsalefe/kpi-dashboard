# backend/app/services/auth_service.py
import sys
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..schemas import RoleEnum as UserRole

# Ajuste de path para imports funcionarem tanto quando executado diretamente 
# quanto quando importado como módulo
if __name__ == "__main__":
    # Quando executado diretamente (python app/services/auth_service.py)
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from app.models import User
    from app.auth import verify_password, get_password_hash, create_access_token
    from app.schemas import UserCreate, UserResponse
else:
    # Quando importado como módulo (from app.services.auth_service import ...)
    from ..models import User
    from ..auth import verify_password, get_password_hash, create_access_token
    from ..schemas import UserCreate, UserResponse


class UserRole(str, Enum):
    """
    Enum para definir os papéis dos usuários no sistema - consistente com schemas.py
    """
    FUNCIONARIO = "Funcionário"  # ← CORRIGIR PARA ISSO
    GESTOR = "Gestor"
    DIRETOR = "Diretor"


class AuthService:
    """
    Serviço de autenticação responsável por:
    - Criação e validação de usuários
    - Login/logout
    - Verificação de permissões
    - Gerenciamento de roles
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_create: UserCreate) -> Dict[str, Any]:
        """
        Cria um novo usuário no sistema
        
        Args:
            user_create: Dados do usuário a ser criado
            
        Returns:
            Dict com status, mensagem e dados do usuário criado
            
        Raises:
            ValueError: Se email já existir ou dados inválidos
        """
        # Verifica se email já existe
        existing_user = self.get_user_by_email(user_create.email)
        if existing_user:
            raise ValueError(f"Email {user_create.email} já está em uso")
        
        # Valida role
        if user_create.role not in [role.value for role in UserRole]:
            raise ValueError(f"Role inválida: {user_create.role}. Opções: {[r.value for r in UserRole]}")
        
        # Cria hash da senha
        hashed_password = get_password_hash(user_create.password)
        
        # Cria usuário
        db_user = User(
            email=user_create.email,
            nome=user_create.nome,
            hashed_password=hashed_password,
            role=user_create.role,
            setor=user_create.setor,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            return {
                "status": "success",
                "message": f"Usuário {user_create.email} criado com sucesso",
                "user": {
                    "id": db_user.id,
                    "email": db_user.email,
                    "nome": db_user.nome,
                    "role": db_user.role,
                    "setor": db_user.setor,
                    "is_active": db_user.is_active,
                    "created_at": db_user.created_at
                }
            }
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Erro ao criar usuário: {str(e)}")
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Autentica um usuário com email e senha
        
        Args:
            email: Email do usuário
            password: Senha em texto plano
            
        Returns:
            User object se autenticação bem-sucedida, None caso contrário
        """
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Atualiza último login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Realiza login e retorna token de acesso
        
        Args:
            email: Email do usuário
            password: Senha em texto plano
            
        Returns:
            Dict com token e dados do usuário
            
        Raises:
            ValueError: Se credenciais inválidas
        """
        user = self.authenticate_user(email, password)
        if not user:
            raise ValueError("Email ou senha inválidos")
        
        # Cria token de acesso
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role}
        )
        
        return {
            "status": "success",
            "message": "Login realizado com sucesso",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "nome": user.nome,
                "role": user.role,
                "setor": user.setor,
                "last_login": user.last_login
            }
        }
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuário por ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def check_permission(self, user: User, required_role: UserRole) -> bool:
        """
        Verifica se o usuário tem permissão para uma ação
        
        Hierarquia de roles:
        - DIRETOR: acesso total
        - GESTOR: acesso ao seu setor + visualização de outros
        - FUNCIONARIO: acesso apenas ao seu setor
        """
        user_role = UserRole(user.role)
        
        # Diretor tem acesso a tudo
        if user_role == UserRole.DIRETOR:
            return True
        
        # Gestor pode fazer ações de gestor e funcionário
        if user_role == UserRole.GESTOR and required_role in [UserRole.GESTOR, UserRole.FUNCIONARIO]:
            return True
        
        # Funcionário só pode fazer ações de funcionário
        if user_role == UserRole.FUNCIONARIO and required_role == UserRole.FUNCIONARIO:
            return True
        
        return False
    
    def can_access_setor(self, user: User, setor: str) -> bool:
        """
        Verifica se o usuário pode acessar dados de um setor específico
        """
        user_role = UserRole(user.role)
        
        # Diretor acessa qualquer setor
        if user_role == UserRole.DIRETOR:
            return True
        
        # Outros roles só acessam o próprio setor
        return user.setor.lower() == setor.lower()
    
    def create_admin_user(self) -> Dict[str, Any]:
        """
        Cria usuário administrador padrão se não existir
        """
        admin_email = "admin@kpidashboard.com"
        existing_admin = self.get_user_by_email(admin_email)
        
        if existing_admin:
            return {
                "status": "info",
                "message": "Usuário administrador já existe",
                "email": admin_email
            }
        
        admin_user = UserCreate(
            email=admin_email,
            nome="Administrador",
            password="admin123",  # Senha padrão - MUDAR EM PRODUÇÃO
            role=UserRole.DIRETOR.value,
            setor="TI"
        )
        
        result = self.create_user(admin_user)
        result["message"] = "Usuário administrador criado com sucesso. ATENÇÃO: Altere a senha padrão!"
        
        return result
    
    def list_users(self, user: User, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Lista usuários (com base nas permissões do usuário solicitante)
        """
        # Verifica permissão
        if not self.check_permission(user, UserRole.GESTOR):
            raise ValueError("Permissão negada para listar usuários")
        
        query = self.db.query(User)
        
        # Se não for diretor, só mostra usuários do mesmo setor
        if user.role != UserRole.DIRETOR.value:
            query = query.filter(User.setor == user.setor)
        
        users = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return {
            "status": "success",
            "total": total,
            "users": [
                {
                    "id": u.id,
                    "email": u.email,
                    "nome": u.nome,
                    "role": u.role,
                    "setor": u.setor,
                    "is_active": u.is_active,
                    "created_at": u.created_at,
                    "last_login": u.last_login
                }
                for u in users
            ]
        }
    
    def deactivate_user(self, user_id: int, admin_user: User) -> Dict[str, Any]:
        """
        Desativa um usuário (soft delete)
        """
        # Só diretor pode desativar usuários
        if not self.check_permission(admin_user, UserRole.DIRETOR):
            raise ValueError("Apenas diretores podem desativar usuários")
        
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        if user.id == admin_user.id:
            raise ValueError("Não é possível desativar o próprio usuário")
        
        user.is_active = False
        self.db.commit()
        
        return {
            "status": "success",
            "message": f"Usuário {user.email} desativado com sucesso"
        }


# Função helper para facilitar o uso
def get_auth_service(db: Session) -> AuthService:
    """Factory function para criar AuthService"""
    return AuthService(db)


# Função de teste do serviço
def test_auth_service():
    """
    Teste básico das funcionalidades do AuthService
    """
    from app.database import SessionLocal
    
    print("=== TESTE AUTH SERVICE ===")
    
    # Testa importações
    print("✓ Importações OK")
    print(f"✓ UserRole definido: {[r.value for r in UserRole]}")
    
    # Testa criação do serviço
    try:
        db = SessionLocal()
        auth_service = AuthService(db)
        print("✓ AuthService criado")
        
        # Testa se pode verificar usuário existente
        test_user = auth_service.get_user_by_email("admin@kpidashboard.com")
        if test_user:
            print(f"✓ Usuário encontrado: {test_user.email} ({test_user.role})")
        else:
            print("ℹ️  Nenhum usuário admin encontrado")
            
        db.close()
        print("✓ Teste concluído com sucesso")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_auth_service()