# backend/app/routers/marketing.py
"""
Router para gerenciamento de dados do setor Marketing.

Endpoints:
- POST /marketing/data - Criar novo registro
- GET /marketing/data - Listar registros (com filtros e paginação)
- GET /marketing/data/{id} - Buscar registro específico
- PUT /marketing/data/{id} - Atualizar registro
- DELETE /marketing/data/{id} - Deletar registro
- GET /marketing/stats - Estatísticas gerais
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract
from typing import List, Optional
from datetime import date, datetime
import json

from app.database import get_db
from app.models import User, MarketingData, AuditLog
from app.schemas import (
    MarketingDataCreate,
    MarketingDataUpdate,
    MarketingDataResponse,
    MarketingFilter
)
from app.auth import get_current_user, require_marketing_access
from app.services.queue_service import queue_service

# Configurar router
router = APIRouter(
    prefix="/marketing",
    tags=["marketing"]
)


# ================ HELPER FUNCTIONS ================

def serialize_for_json(obj):
    """Converter objetos Python para tipos serializáveis em JSON"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    return obj


def create_audit_log(
    db: Session,
    user: User,
    acao: str,
    tabela: str,
    registro_id: Optional[int] = None,
    dados_antes: Optional[dict] = None,
    dados_depois: Optional[dict] = None
):
    """Criar registro de auditoria"""
    audit = AuditLog(
        user_id=user.id,
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        dados_antes=json.dumps(serialize_for_json(dados_antes)) if dados_antes else None,
        dados_depois=json.dumps(serialize_for_json(dados_depois)) if dados_depois else None,
        timestamp=datetime.utcnow()
    )
    db.add(audit)


def check_duplicate(
    db: Session,
    data_ref: date,
    canal: str,
    campanha: str,
    exclude_id: Optional[int] = None
) -> bool:
    """Verificar se já existe registro com mesma chave natural"""
    query = db.query(MarketingData).filter(
        and_(
            MarketingData.data_ref == data_ref,
            MarketingData.canal == canal,
            MarketingData.campanha == campanha
        )
    )
    
    if exclude_id:
        query = query.filter(MarketingData.id != exclude_id)
    
    return query.first() is not None


# ================ ENDPOINTS CRUD ================

@router.post("/data", response_model=MarketingDataResponse, status_code=status.HTTP_201_CREATED)
def create_marketing_data(
    data: MarketingDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_marketing_access())
):
    """
    Criar novo registro de dados de Marketing
    
    - **data_ref**: Data de referência do dado (YYYY-MM-DD)
    - **canal**: Canal de marketing (Facebook, Google, Instagram, etc.)
    - **campanha**: Nome da campanha
    - **investimento**: Valor investido (sem R$)
    - Outros campos opcionais: impressoes, cliques, conversoes, leads, vendas, receita
    
    **Anti-duplicidade**: Não permite registros duplicados com mesma data_ref + canal + campanha
    """
    # Verificar duplicidade
    if check_duplicate(db, data.data_ref, data.canal, data.campanha):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe registro para {data.data_ref} - {data.canal} - {data.campanha}"
        )
    
    # Criar registro
    db_data = MarketingData(
        **data.model_dump(),
        user_id=current_user.id
    )
    
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    
    # Auditoria
    create_audit_log(
        db=db,
        user=current_user,
        acao="CREATE",
        tabela="marketing_data",
        registro_id=db_data.id,
        dados_depois=data.model_dump()
    )
    db.commit()
    
    # Enfileirar job de cálculo de KPI (assíncrono)
    try:
        queue_service.add_kpi_job(
            sector="marketing",
            action="calculate",
            data_id=db_data.id,
            date_ref=str(db_data.data_ref),
            user_id=current_user.id
        )
    except Exception as e:
        print(f"⚠️ Erro ao enfileirar job: {e}")
    
    return db_data


@router.get("/data", response_model=dict)
def list_marketing_data(
    # Filtros
    data_inicio: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    canal: Optional[str] = Query(None, description="Filtrar por canal"),
    campanha: Optional[str] = Query(None, description="Buscar por nome de campanha (parcial)"),
    # Paginação
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(50, ge=1, le=100, description="Items por página"),
    # Ordenação
    sort_by: str = Query("data_ref", description="Campo para ordenar"),
    sort_order: str = Query("desc", description="Ordem: asc ou desc"),
    # Auth
    db: Session = Depends(get_db),
    current_user: User = Depends(require_marketing_access())
):
    """
    Listar dados de Marketing com filtros e paginação
    
    **Filtros disponíveis:**
    - data_inicio / data_fim: Período
    - canal: Canal específico
    - campanha: Busca parcial no nome da campanha
    
    **Paginação:**
    - page: Número da página (padrão: 1)
    - per_page: Items por página (padrão: 50, máx: 100)
    
    **Ordenação:**
    - sort_by: Campo para ordenar (padrão: data_ref)
    - sort_order: asc ou desc (padrão: desc)
    """
    # Query base
    query = db.query(MarketingData)
    
    # Aplicar filtros
    filters = []
    
    if data_inicio:
        filters.append(MarketingData.data_ref >= data_inicio)
    
    if data_fim:
        filters.append(MarketingData.data_ref <= data_fim)
    
    if canal:
        filters.append(MarketingData.canal == canal)
    
    if campanha:
        filters.append(MarketingData.campanha.ilike(f"%{campanha}%"))
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Total de registros (antes da paginação)
    total = query.count()
    
    # Ordenação
    sort_column = getattr(MarketingData, sort_by, MarketingData.data_ref)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Paginação
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    
    # Calcular totais de páginas
    total_pages = (total + per_page - 1) // per_page
    
    return {
        "status": "success",
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": [MarketingDataResponse.model_validate(item) for item in items],
        "filters_applied": {
            "data_inicio": data_inicio.isoformat() if data_inicio else None,
            "data_fim": data_fim.isoformat() if data_fim else None,
            "canal": canal,
            "campanha": campanha
        }
    }


@router.get("/data/{data_id}", response_model=MarketingDataResponse)
def get_marketing_data(
    data_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_marketing_access())
):
    """
    Buscar registro específico por ID
    """
    data = db.query(MarketingData).filter(MarketingData.id == data_id).first()
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro {data_id} não encontrado"
        )
    
    return data


@router.put("/data/{data_id}", response_model=MarketingDataResponse)
def update_marketing_data(
    data_id: int,
    data_update: MarketingDataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_marketing_access())
):
    """
    Atualizar registro existente
    
    Apenas campos fornecidos serão atualizados.
    Não é possível alterar data_ref, canal ou campanha (chave natural).
    """
    # Buscar registro
    db_data = db.query(MarketingData).filter(MarketingData.id == data_id).first()
    
    if not db_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro {data_id} não encontrado"
        )
    
    # Guardar dados antes da alteração (para auditoria)
    dados_antes = {
        "canal": db_data.canal,
        "campanha": db_data.campanha,
        "investimento": db_data.investimento,
        "impressoes": db_data.impressoes,
        "cliques": db_data.cliques,
        "conversoes": db_data.conversoes,
        "leads": db_data.leads,
        "vendas": db_data.vendas,
        "receita": db_data.receita
    }
    
    # Atualizar apenas campos fornecidos
    update_data = data_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_data, field, value)
    
    db_data.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_data)
    
    # Auditoria
    create_audit_log(
        db=db,
        user=current_user,
        acao="UPDATE",
        tabela="marketing_data",
        registro_id=data_id,
        dados_antes=dados_antes,
        dados_depois=update_data
    )
    db.commit()
    
    return db_data


@router.delete("/data/{data_id}", status_code=status.HTTP_200_OK)
def delete_marketing_data(
    data_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_marketing_access())
):
    """
    Deletar registro
    
    **Atenção**: Esta ação é irreversível.
    """
    # Buscar registro
    db_data = db.query(MarketingData).filter(MarketingData.id == data_id).first()
    
    if not db_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro {data_id} não encontrado"
        )
    
    # Guardar dados para auditoria
    dados_antes = {
        "data_ref": db_data.data_ref.isoformat(),
        "canal": db_data.canal,
        "campanha": db_data.campanha,
        "investimento": db_data.investimento
    }
    
    # Deletar
    db.delete(db_data)
    
    # Auditoria
    create_audit_log(
        db=db,
        user=current_user,
        acao="DELETE",
        tabela="marketing_data",
        registro_id=data_id,
        dados_antes=dados_antes
    )
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Registro {data_id} deletado com sucesso"
    }


# ================ ENDPOINTS DE ESTATÍSTICAS ================

@router.get("/stats", response_model=dict)
def get_marketing_stats(
    data_inicio: Optional[date] = Query(None, description="Data inicial"),
    data_fim: Optional[date] = Query(None, description="Data final"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_marketing_access())
):
    """
    Obter estatísticas gerais de Marketing
    
    Retorna:
    - Total de investimento
    - Total de leads gerados
    - Total de vendas
    - Receita total
    - ROI (Return on Investment)
    - CPL (Custo por Lead)
    - Taxa de conversão
    - Distribuição por canal
    """
    # Query base
    query = db.query(MarketingData)
    
    # Aplicar filtro de período se fornecido
    if data_inicio:
        query = query.filter(MarketingData.data_ref >= data_inicio)
    if data_fim:
        query = query.filter(MarketingData.data_ref <= data_fim)
    
    # Agregações
    stats = query.with_entities(
        func.sum(MarketingData.investimento).label("total_investimento"),
        func.sum(MarketingData.impressoes).label("total_impressoes"),
        func.sum(MarketingData.cliques).label("total_cliques"),
        func.sum(MarketingData.conversoes).label("total_conversoes"),
        func.sum(MarketingData.leads).label("total_leads"),
        func.sum(MarketingData.vendas).label("total_vendas"),
        func.sum(MarketingData.receita).label("total_receita"),
        func.count(MarketingData.id).label("total_registros")
    ).first()
    
    # Distribuição por canal
    por_canal = query.with_entities(
        MarketingData.canal,
        func.sum(MarketingData.investimento).label("investimento"),
        func.sum(MarketingData.leads).label("leads"),
        func.sum(MarketingData.vendas).label("vendas"),
        func.sum(MarketingData.receita).label("receita")
    ).group_by(MarketingData.canal).all()
    
    # Calcular métricas derivadas
    total_investimento = float(stats.total_investimento or 0)
    total_leads = int(stats.total_leads or 0)
    total_vendas = int(stats.total_vendas or 0)
    total_receita = float(stats.total_receita or 0)
    total_cliques = int(stats.total_cliques or 0)
    total_impressoes = int(stats.total_impressoes or 0)
    
    # ROI (Return on Investment) = (Receita - Investimento) / Investimento * 100
    roi = ((total_receita - total_investimento) / total_investimento * 100) if total_investimento > 0 else 0
    
    # CPL (Custo por Lead) = Investimento / Leads
    cpl = (total_investimento / total_leads) if total_leads > 0 else 0
    
    # Taxa de conversão = Vendas / Leads * 100
    taxa_conversao = (total_vendas / total_leads * 100) if total_leads > 0 else 0
    
    # CTR (Click-through Rate) = Cliques / Impressões * 100
    ctr = (total_cliques / total_impressoes * 100) if total_impressoes > 0 else 0
    
    return {
        "status": "success",
        "periodo": {
            "data_inicio": data_inicio.isoformat() if data_inicio else None,
            "data_fim": data_fim.isoformat() if data_fim else None
        },
        "totais": {
            "registros": stats.total_registros,
            "investimento": round(total_investimento, 2),
            "impressoes": total_impressoes,
            "cliques": total_cliques,
            "conversoes": int(stats.total_conversoes or 0),
            "leads": total_leads,
            "vendas": total_vendas,
            "receita": round(total_receita, 2)
        },
        "metricas": {
            "roi_percentual": round(roi, 2),
            "cpl": round(cpl, 2),
            "taxa_conversao_percentual": round(taxa_conversao, 2),
            "ctr_percentual": round(ctr, 2),
            "ticket_medio": round(total_receita / total_vendas, 2) if total_vendas > 0 else 0
        },
        "por_canal": [
            {
                "canal": canal,
                "investimento": round(float(inv or 0), 2),
                "leads": int(leads or 0),
                "vendas": int(vendas or 0),
                "receita": round(float(rec or 0), 2),
                "roi": round(((float(rec or 0) - float(inv or 0)) / float(inv or 0) * 100) if inv and inv > 0 else 0, 2)
            }
            for canal, inv, leads, vendas, rec in por_canal
        ]
    }


@router.get("/health")
def marketing_health():
    """Health check do router Marketing"""
    return {
        "status": "healthy",
        "router": "marketing",
        "endpoints": [
            "POST /marketing/data - Criar registro",
            "GET /marketing/data - Listar registros",
            "GET /marketing/data/{id} - Buscar registro",
            "PUT /marketing/data/{id} - Atualizar registro",
            "DELETE /marketing/data/{id} - Deletar registro",
            "GET /marketing/stats - Estatísticas"
        ]
    }