# backend/app/main.py
"""
FastAPI application principal para o KPI Dashboard.
Integra todas as funcionalidades: config, database, auth, WebSocket e health checks.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import json
from typing import List

# Imports dos módulos do projeto
from app.config import settings
from app.database import test_connection, get_db_info, get_table_info
from app.routers import auth

# Criar aplicação FastAPI com configurações do settings
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Sistema de Dashboard KPI para gestão de dados por setores com real-time updates",
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Configurar CORS usando settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth.router, prefix="/api")

# Gerenciador de conexões WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket conectado. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"WebSocket desconectado. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Envia mensagem para todos os clientes conectados"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Remove conexões mortas
        for conn in disconnected:
            self.disconnect(conn)

# Instância global do gerenciador
manager = ConnectionManager()

# ================ ENDPOINTS PRINCIPAIS ================

@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "environment": settings.environment,
        "debug": settings.DEBUG,
        "timezone": settings.TIMEZONE,
        "docs": "/docs" if settings.DEBUG else "disabled",
        "health": "/health",
        "api_info": "/api/info",
        "auth": "/api/auth/health",
        "websocket": "/ws",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check completo da aplicação"""
    # Verifica conexão com banco
    db_connected = test_connection()
    db_info = get_db_info() if db_connected else {"status": "disconnected"}
    table_info = get_table_info() if db_connected else {"status": "unavailable"}
    
    # Status geral
    status = "healthy" if db_connected else "unhealthy"
    
    return {
        "status": status,
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.environment,
        "debug": settings.DEBUG,
        "timezone": settings.TIMEZONE,
        "timestamp": datetime.now().isoformat(),
        "database": {
            "connected": db_connected,
            "info": db_info,
            "tables": table_info
        },
        "services": {
            "auth": "available",
            "websocket": f"{len(manager.active_connections)} connections"
        },
        "cors_origins": settings.CORS_ORIGINS
    }


@app.get("/api/info")
async def api_info():
    """Informações detalhadas sobre a API e endpoints"""
    return {
        "api_version": "v1",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "available_endpoints": {
            "authentication": {
                "base": "/api/auth",
                "endpoints": [
                    "POST /api/auth/register - Registrar usuário",
                    "POST /api/auth/login - Login",
                    "GET /api/auth/me - Info do usuário atual",
                    "POST /api/auth/logout - Logout",
                    "POST /api/auth/create-admin - Criar admin inicial",
                    "GET /api/auth/users - Listar usuários",
                    "PATCH /api/auth/users/{id}/deactivate - Desativar usuário",
                    "GET /api/auth/check-permissions - Verificar permissões",
                    "GET /api/auth/health - Health check auth"
                ]
            },
            "general": [
                "GET / - Info básica",
                "GET /health - Health check completo", 
                "GET /api/info - Esta página",
                "POST /api/test-broadcast - Teste WebSocket",
                "WebSocket /ws - Real-time updates"
            ]
        },
        "setores_suportados": [
            "marketing",
            "comercial", 
            "eventos",
            "rh",
            "pedagogico",
            "financeiro"
        ],
        "user_roles": [
            "funcionario - Acesso ao próprio setor",
            "gestor - Acesso ao setor + gerenciar usuários",
            "diretor - Acesso total"
        ]
    }


# ================ WEBSOCKET ================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint para comunicação em tempo real
    
    Usado para:
    - Notificações de novos dados
    - Atualizações de KPIs em tempo real
    - Alertas de metas atingidas
    """
    await manager.connect(websocket)
    try:
        # Mensagem de boas-vindas
        welcome_message = {
            "type": "welcome",
            "message": f"Conectado ao {settings.APP_NAME}",
            "timestamp": datetime.now().isoformat(),
            "server_timezone": settings.TIMEZONE
        }
        await manager.send_personal_message(json.dumps(welcome_message), websocket)
        
        # Manter conexão ativa
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Responder com echo (para teste)
                response = {
                    "type": "echo",
                    "original_message": message,
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(response), websocket)
                
            except json.JSONDecodeError:
                # Se não for JSON válido, echo simples
                await manager.send_personal_message(f"Echo: {data}", websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/test-broadcast")
async def test_broadcast():
    """Endpoint de teste para WebSocket broadcast"""
    message = {
        "type": "test_kpi_update",
        "setor": "marketing",
        "data": {
            "kpi": "conversao_leads",
            "value": 23.5,
            "meta": 25.0,
            "status": "warning",
            "timestamp": datetime.now().isoformat()
        },
        "broadcast_info": {
            "sent_to_connections": len(manager.active_connections),
            "server_time": datetime.now().isoformat()
        }
    }
    
    await manager.broadcast(message)
    
    return {
        "status": "success",
        "message": "Broadcast de teste enviado",
        "connections": len(manager.active_connections),
        "data_sent": message
    }


# ================ HANDLERS DE EXCEÇÃO ================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint não encontrado",
            "message": f"O endpoint {request.url.path} não existe",
            "suggestion": "Consulte /api/info para ver endpoints disponíveis",
            "docs": "/docs" if settings.DEBUG else "disabled",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "message": "Ocorreu um erro inesperado",
            "debug_info": str(exc) if settings.DEBUG else "Detalhes não disponíveis em produção",
            "timestamp": datetime.now().isoformat()
        }
    )


# ================ FUNÇÃO HELPER PARA KPI UPDATES ================

async def broadcast_kpi_update(setor: str, kpi_name: str, kpi_data: dict):
    """
    Função helper para enviar atualizações de KPI via WebSocket
    
    Args:
        setor: Nome do setor (marketing, comercial, etc.)
        kpi_name: Nome do KPI
        kpi_data: Dados do KPI (value, meta, status, etc.)
    """
    message = {
        "type": "kpi_update",
        "setor": setor,
        "kpi": kpi_name,
        "data": kpi_data,
        "timestamp": datetime.now().isoformat(),
        "timezone": settings.TIMEZONE
    }
    
    await manager.broadcast(message)


# ================ STARTUP/SHUTDOWN EVENTS ================

@app.on_event("startup")
async def startup_event():
    """Executado na inicialização da aplicação"""
    print(f"🚀 {settings.APP_NAME} v{settings.VERSION} iniciando...")
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Timezone: {settings.TIMEZONE}")
    
    # Testa conexão com banco
    if test_connection():
        print("✅ Conexão com PostgreSQL OK")
        db_info = get_db_info()
        if db_info["status"] == "connected":
            print(f"Database: {db_info['database']} | User: {db_info['user']}")
    else:
        print("❌ Falha na conexão com PostgreSQL")
    
    print(f"CORS Origins: {settings.CORS_ORIGINS}")
    print("Servidor pronto!")


@app.on_event("shutdown")
async def shutdown_event():
    """Executado no shutdown da aplicação"""
    print("🛑 Encerrando aplicação...")
    
    # Notifica clientes WebSocket conectados
    if manager.active_connections:
        shutdown_message = {
            "type": "server_shutdown",
            "message": "Servidor sendo desligado",
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(shutdown_message)
    
    print("Aplicação encerrada")


# ================ EXECUÇÃO DIRETA ================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.log_level.lower(),
        timezone=settings.TIMEZONE
    )