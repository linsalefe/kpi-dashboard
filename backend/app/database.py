# backend/app/database.py
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

# Ajuste de path para imports funcionarem tanto quando executado diretamente 
# quanto quando importado como módulo
if __name__ == "__main__":
    # Quando executado diretamente (python app/database.py)
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config import settings
else:
    # Quando importado como módulo (from app.database import ...)
    from .config import settings

# Criar engine do SQLAlchemy usando a URL do config
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries em modo debug
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verifica conexões antes de usar
    pool_recycle=3600    # Recicla conexões a cada hora
)

# Criar sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos - usando SQLAlchemy 2.0 syntax
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependência para obter sessão do banco de dados.
    Usado com FastAPI Depends() para injeção de dependência.
    
    Yields:
        Session: Sessão ativa do SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Cria todas as tabelas no banco de dados.
    Usado principalmente para desenvolvimento/testes.
    Em produção, use migrações do Alembic.
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Remove todas as tabelas do banco de dados.
    ⚠️ CUIDADO: Isso apaga todos os dados!
    Usado apenas para desenvolvimento/testes.
    """
    Base.metadata.drop_all(bind=engine)


def test_connection():
    """
    Testa a conexão com o banco de dados.
    
    Returns:
        bool: True se conexão bem-sucedida, False caso contrário
    """
    try:
        # SQLAlchemy 2.0: usar text() para SQL raw
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        print(f"Erro ao conectar com o banco: {e}")
        return False


def get_db_info():
    """
    Retorna informações sobre o banco de dados.
    
    Returns:
        dict: Informações da conexão (sem dados sensíveis)
    """
    try:
        with engine.connect() as connection:
            # SQLAlchemy 2.0: usar text() para todos os SQL raw
            
            # Pega informações básicas do PostgreSQL
            version_result = connection.execute(text("SELECT version()"))
            version = version_result.fetchone()[0]
            
            # Pega nome do banco atual
            db_result = connection.execute(text("SELECT current_database()"))
            database = db_result.fetchone()[0]
            
            # Pega usuário atual
            user_result = connection.execute(text("SELECT current_user"))
            user = user_result.fetchone()[0]
            
            return {
                "status": "connected",
                "database": database,
                "user": user,
                "version": version.split()[0:2],  # PostgreSQL e versão
                "engine_info": {
                    "pool_size": engine.pool.size(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow(),
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_table_info():
    """
    Retorna informações sobre as tabelas existentes no banco
    """
    try:
        with engine.connect() as connection:
            # Lista todas as tabelas do schema público
            tables_query = text("""
                SELECT 
                    table_name,
                    table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            result = connection.execute(tables_query)
            tables = [{"name": row[0], "type": row[1]} for row in result.fetchall()]
            
            return {
                "status": "success",
                "count": len(tables),
                "tables": tables
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Context manager para transações manuais
class DatabaseTransaction:
    """
    Context manager para gerenciar transações do banco de dados manualmente.
    
    Exemplo de uso:
        with DatabaseTransaction() as db:
            user = User(email="test@example.com")
            db.add(user)
            # Commit automático se não houver exceção
            # Rollback automático se houver exceção
    """
    
    def __init__(self):
        self.db: Session = None
    
    def __enter__(self) -> Session:
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Se houve exceção, faz rollback
            self.db.rollback()
        else:
            # Se não houve exceção, faz commit
            self.db.commit()
        
        self.db.close()


if __name__ == "__main__":
    # Teste básico da conexão
    print("=== TESTE DE CONEXÃO COM BANCO ===")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    if test_connection():
        print("✓ Conexão com banco bem-sucedida!")
        
        info = get_db_info()
        if info["status"] == "connected":
            print(f"Database: {info['database']}")
            print(f"User: {info['user']}")
            print(f"Version: {' '.join(info['version'])}")
            print(f"Pool info: {info['engine_info']}")
            
            # Mostra tabelas existentes
            print("\n=== TABELAS NO BANCO ===")
            table_info = get_table_info()
            if table_info["status"] == "success":
                print(f"Total de tabelas: {table_info['count']}")
                for table in table_info["tables"]:
                    print(f"  - {table['name']} ({table['type']})")
            else:
                print(f"Erro ao listar tabelas: {table_info['error']}")
                
        else:
            print(f"Erro ao obter informações: {info['error']}")
    else:
        print("❌ Falha na conexão com banco!")
        
    # Teste adicional de importação
    print("\n=== TESTE DE IMPORTAÇÃO ===")
    try:
        print("✓ Config carregado")
        print("✓ Engine criado")
        print("✓ SessionLocal configurado")
        print("✓ Base declarativa pronta (SQLAlchemy 2.0)")
        print("✓ Função get_db definida")
    except Exception as e:
        print(f"❌ Erro: {e}")