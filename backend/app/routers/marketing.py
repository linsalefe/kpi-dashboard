from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import date, datetime, timedelta
import json

from app.database import get_db
from app.models import MarketingData, User, AuditLog
from app.schemas import MarketingCreate, MarketingResponse, MarketingUpdate
from app.auth import get_current_user
from app.services.queue_service import QueueService

router = APIRouter(prefix="/marketing", tags=["Marketing"])


@router.post("/", response_model=MarketingResponse, status_code=status.HTTP_201_CREATED)
async def create_marketing_data(
    data: MarketingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria um novo registro de dados de marketing.
    
    Anti-duplicidade: data_ref + canal + campanha + produto
    """
    # Verificar duplicidade (chave natural: data_ref + canal + campanha + produto)
    existing = db.query(MarketingData).filter(
        and_(
            MarketingData.data_ref == data.data_ref,
            MarketingData.canal == data.canal,
            MarketingData.campanha == data.campanha,
            MarketingData.produto == data.produto
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um registro para {data.data_ref} - {data.produto} - {data.canal} - {data.campanha}"
        )
    
    # Criar registro
    db_data = MarketingData(
        **data.model_dump(),
        created_by=current_user.id
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    
    # Auditoria
    audit = AuditLog(
        user_id=current_user.id,
        action="CREATE",
        table_name="marketing_data",
        record_id=db_data.id,
        new_values=json.dumps(data.model_dump(), default=str)
    )
    db.add(audit)
    db.commit()
    
    # Enfileirar job de cálculo de KPIs
    try:
        queue_service = QueueService()
        await queue_service.enqueue_marketing_kpis(db_data.id)
    except Exception as e:
        print(f"Erro ao enfileirar job: {e}")
    
    return db_data


@router.get("/", response_model=List[MarketingResponse])
async def list_marketing_data(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    canal: Optional[str] = None,
    produto: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista registros de marketing com filtros opcionais.
    """
    query = db.query(MarketingData)
    
    if data_inicio:
        query = query.filter(MarketingData.data_ref >= data_inicio)
    if data_fim:
        query = query.filter(MarketingData.data_ref <= data_fim)
    if canal:
        query = query.filter(MarketingData.canal == canal)
    if produto:
        query = query.filter(MarketingData.produto == produto)
    
    return query.order_by(MarketingData.data_ref.desc()).offset(skip).limit(limit).all()


@router.get("/stats")
async def get_marketing_stats(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    produto: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna estatísticas agregadas de marketing.
    
    KPIs por produto:
    - Congressos: CPA (custo por venda)
    - Pós-Graduações: CPL (custo por lead)
    - Cursos Hotmart: CPA (custo por venda)
    - Seminário: CPA (custo por venda)
    - Intercâmbios: CPL (custo por lead)
    """
    query = db.query(MarketingData)
    
    # Filtros
    if data_inicio:
        query = query.filter(MarketingData.data_ref >= data_inicio)
    if data_fim:
        query = query.filter(MarketingData.data_ref <= data_fim)
    if produto:
        query = query.filter(MarketingData.produto == produto)
    
    # Agregações
    stats = query.with_entities(
        func.sum(MarketingData.investimento).label('investimento_total'),
        func.sum(MarketingData.impressoes).label('impressoes_total'),
        func.sum(MarketingData.cliques).label('cliques_total'),
        func.sum(MarketingData.leads).label('leads_total'),
        func.sum(MarketingData.vendas).label('vendas_total'),
        func.sum(MarketingData.receita).label('receita_total'),
        func.count(MarketingData.id).label('total_registros')
    ).first()
    
    investimento = float(stats.investimento_total or 0)
    impressoes = int(stats.impressoes_total or 0)
    cliques = int(stats.cliques_total or 0)
    leads = int(stats.leads_total or 0)
    vendas = int(stats.vendas_total or 0)
    receita = float(stats.receita_total or 0)
    total_registros = int(stats.total_registros or 0)
    
    # Cálculo de KPIs
    ctr = round((cliques / impressoes * 100), 2) if impressoes > 0 else 0
    taxa_conversao = round((leads / cliques * 100), 2) if cliques > 0 else 0
    cpl = round((investimento / leads), 2) if leads > 0 else 0
    cpa = round((investimento / vendas), 2) if vendas > 0 else 0
    roi = round(((receita - investimento) / investimento * 100), 2) if investimento > 0 else 0
    roas = round((receita / investimento), 2) if investimento > 0 else 0
    
    return {
        "periodo": {
            "data_inicio": data_inicio.isoformat() if data_inicio else None,
            "data_fim": data_fim.isoformat() if data_fim else None,
            "produto": produto
        },
        "totais": {
            "investimento": investimento,
            "impressoes": impressoes,
            "cliques": cliques,
            "leads": leads,
            "vendas": vendas,
            "receita": receita,
            "total_registros": total_registros
        },
        "kpis": {
            "ctr": ctr,
            "taxa_conversao": taxa_conversao,
            "cpl": cpl,
            "cpa": cpa,
            "roi": roi,
            "roas": roas
        }
    }


@router.get("/{id}", response_model=MarketingResponse)
async def get_marketing_data(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna um registro específico de marketing.
    """
    data = db.query(MarketingData).filter(MarketingData.id == id).first()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado"
        )
    return data


@router.put("/{id}", response_model=MarketingResponse)
async def update_marketing_data(
    id: int,
    data: MarketingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza um registro de marketing existente.
    """
    db_data = db.query(MarketingData).filter(MarketingData.id == id).first()
    if not db_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado"
        )
    
    # Guardar valores antigos para auditoria
    old_values = {
        "data_ref": str(db_data.data_ref),
        "produto": db_data.produto,
        "canal": db_data.canal,
        "campanha": db_data.campanha,
        "investimento": db_data.investimento,
        "impressoes": db_data.impressoes,
        "cliques": db_data.cliques,
        "leads": db_data.leads,
        "vendas": db_data.vendas,
        "receita": db_data.receita
    }
    
    # Atualizar apenas campos fornecidos
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_data, field, value)
    
    db_data.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_data)
    
    # Auditoria
    audit = AuditLog(
        user_id=current_user.id,
        action="UPDATE",
        table_name="marketing_data",
        record_id=db_data.id,
        old_values=json.dumps(old_values),
        new_values=json.dumps(update_data, default=str)
    )
    db.add(audit)
    db.commit()
    
    # Enfileirar recálculo de KPIs
    try:
        queue_service = QueueService()
        await queue_service.enqueue_marketing_kpis(db_data.id)
    except Exception as e:
        print(f"Erro ao enfileirar job: {e}")
    
    return db_data


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_marketing_data(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deleta um registro de marketing.
    """
    db_data = db.query(MarketingData).filter(MarketingData.id == id).first()
    if not db_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado"
        )
    
    # Auditoria antes de deletar
    old_values = {
        "data_ref": str(db_data.data_ref),
        "produto": db_data.produto,
        "canal": db_data.canal,
        "campanha": db_data.campanha,
        "investimento": db_data.investimento
    }
    
    audit = AuditLog(
        user_id=current_user.id,
        action="DELETE",
        table_name="marketing_data",
        record_id=db_data.id,
        old_values=json.dumps(old_values)
    )
    db.add(audit)
    
    db.delete(db_data)
    db.commit()
    
    return None
