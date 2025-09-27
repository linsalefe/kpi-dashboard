# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """
    Configurações da aplicação usando Pydantic Settings v2.
    Inclui TODOS os campos do arquivo .env para evitar erros de validação.
    """
    
    # Environment
    environment: str = "development"
    debug: str = "true"  # Campo que estava faltando
    
    # Database individual fields (from .env)
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "kpi_dashboard"
    db_user: str = "postgres"
    db_password: str = "postgres"
    
    # Redis individual fields (from .env)
    redis_host: str = "localhost"
    redis_port: str = "6379"
    redis_db: str = "0"
    redis_password: str = ""
    
    # JWT (mapping from jwt_secret in .env to SECRET_KEY)
    jwt_secret: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS (from cors_origins in .env)
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    
    # File upload
    max_file_size_mb: str = "10"
    upload_folder: str = "./uploads"
    
    # Logging
    log_level: str = "INFO"
    
    # App
    APP_NAME: str = "KPI Dashboard"
    VERSION: str = "1.0.0"
    
    # Timezone
    TIMEZONE: str = "America/Fortaleza"
    
    # Computed properties para compatibilidade com o resto da aplicação
    @property
    def SECRET_KEY(self) -> str:
        """Alias para jwt_secret para compatibilidade com o resto da aplicação"""
        return self.jwt_secret
    
    @property
    def DATABASE_URL(self) -> str:
        """Constrói a URL do banco a partir dos campos individuais"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def REDIS_URL(self) -> str:
        """Constrói a URL do Redis a partir dos campos individuais"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Converte a string de origins em lista"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def DEBUG(self) -> bool:
        """Converte string debug em boolean"""
        return self.debug.lower() in ["true", "1", "yes", "on"]
    
    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        """Converte MB para bytes"""
        return int(self.max_file_size_mb) * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância global das configurações
settings = Settings()


# Função helper para debug das configurações
def print_settings():
    """
    Função para debug - mostra as configurações carregadas
    (sem mostrar dados sensíveis como SECRET_KEY)
    """
    print(f"=== {settings.APP_NAME} v{settings.VERSION} ===")
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.DEBUG} (raw: {settings.debug})")
    print(f"Database: {settings.db_user}@{settings.db_host}:{settings.db_port}/{settings.db_name}")
    print(f"Redis: {settings.redis_host}:{settings.redis_port}/{settings.redis_db}")
    print(f"CORS Origins: {settings.CORS_ORIGINS}")
    print(f"Upload folder: {settings.upload_folder}")
    print(f"Max file size: {settings.max_file_size_mb}MB ({settings.MAX_FILE_SIZE_BYTES} bytes)")
    print(f"Log level: {settings.log_level}")
    print(f"Timezone: {settings.TIMEZONE}")
    print(f"Token Expire: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")


def validate_settings():
    """
    Valida se as configurações essenciais estão corretas
    """
    print("\n=== VALIDANDO CONFIGURAÇÕES ===")
    errors = []
    
    # Verifica se o banco pode ser acessado
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password
        )
        conn.close()
        print("✓ Conexão com PostgreSQL OK")
    except Exception as e:
        errors.append(f"✗ Erro PostgreSQL: {e}")
    
    # Verifica diretório de upload
    if not os.path.exists(settings.upload_folder):
        try:
            os.makedirs(settings.upload_folder)
            print(f"✓ Diretório {settings.upload_folder} criado")
        except Exception as e:
            errors.append(f"✗ Erro ao criar diretório upload: {e}")
    else:
        print(f"✓ Diretório {settings.upload_folder} já existe")
    
    # Verifica se CORS tem pelo menos uma origem
    if len(settings.CORS_ORIGINS) == 0:
        errors.append("✗ Erro: Nenhuma origem CORS configurada")
    else:
        print(f"✓ CORS configurado com {len(settings.CORS_ORIGINS)} origins")
    
    # Verifica se SECRET_KEY não é o padrão
    if settings.SECRET_KEY == "your-secret-key-change-in-production":
        print("⚠️  WARNING: SECRET_KEY usando valor padrão (OK para desenvolvimento)")
    else:
        print("✓ SECRET_KEY personalizada configurada")
    
    return errors


if __name__ == "__main__":
    # Teste das configurações
    try:
        print_settings()
        errors = validate_settings()
        
        if errors:
            print("\n❌ ERROS ENCONTRADOS:")
            for error in errors:
                print(error)
        else:
            print("\n✅ Todas as configurações estão válidas!")
            print("\nTeste rápido:")
            print(f"  DATABASE_URL: {settings.DATABASE_URL}")
            print(f"  REDIS_URL: {settings.REDIS_URL}")
            print(f"  CORS_ORIGINS: {settings.CORS_ORIGINS}")
        
    except Exception as e:
        print(f"❌ ERRO FATAL ao carregar configurações: {e}")