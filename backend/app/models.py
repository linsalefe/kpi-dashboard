from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nome = Column(String(255), nullable=False)
    cargo = Column(String(100))
    setor = Column(String(50))
    role = Column(String(20))
    ativo = Column(Boolean, default=True)  # CORRIGIDO: era is_active
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MarketingData(Base):
    __tablename__ = "marketing_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False, index=True)
    produto = Column(String(50), nullable=False, index=True)
    canal = Column(String(100), nullable=False, index=True)
    campanha = Column(String(255), nullable=False)
    investimento = Column(Float, nullable=False)
    impressoes = Column(Integer, nullable=False, default=0)
    cliques = Column(Integer, nullable=False, default=0)
    leads = Column(Integer, nullable=False, default=0)
    vendas = Column(Integer, nullable=False, default=0)
    receita = Column(Float, nullable=False, default=0.0)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('investimento >= 0', name='check_marketing_investimento_positive'),
        CheckConstraint('impressoes >= 0', name='check_marketing_impressoes_positive'),
        CheckConstraint('cliques >= 0', name='check_marketing_cliques_positive'),
        CheckConstraint('leads >= 0', name='check_marketing_leads_positive'),
        CheckConstraint('vendas >= 0', name='check_marketing_vendas_positive'),
        CheckConstraint('receita >= 0', name='check_marketing_receita_positive'),
    )


class ComercialData(Base):
    __tablename__ = "comercial_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False, index=True)
    vendedor = Column(String(255), nullable=False, index=True)
    produto = Column(String(255), nullable=False)
    quantidade = Column(Integer, nullable=False, default=0)
    valor_total = Column(Float, nullable=False, default=0.0)
    comissao = Column(Float, nullable=False, default=0.0)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventosData(Base):
    __tablename__ = "eventos_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False, index=True)
    nome_evento = Column(String(255), nullable=False)
    tipo_evento = Column(String(100), nullable=False)
    participantes = Column(Integer, nullable=False, default=0)
    custo_total = Column(Float, nullable=False, default=0.0)
    receita = Column(Float, nullable=False, default=0.0)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RHData(Base):
    __tablename__ = "rh_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False, index=True)
    departamento = Column(String(100), nullable=False, index=True)
    total_funcionarios = Column(Integer, nullable=False, default=0)
    admissoes = Column(Integer, nullable=False, default=0)
    demissoes = Column(Integer, nullable=False, default=0)
    horas_treinamento = Column(Float, nullable=False, default=0.0)
    custo_total = Column(Float, nullable=False, default=0.0)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PedagogicoData(Base):
    __tablename__ = "pedagogico_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False, index=True)
    curso = Column(String(255), nullable=False, index=True)
    turma = Column(String(100), nullable=False)
    alunos_matriculados = Column(Integer, nullable=False, default=0)
    frequencia_media = Column(Float, nullable=False, default=0.0)
    nota_media = Column(Float, nullable=False, default=0.0)
    evasao = Column(Integer, nullable=False, default=0)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FinanceiroData(Base):
    __tablename__ = "financeiro_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False, index=True)
    categoria = Column(String(100), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)
    valor = Column(Float, nullable=False)
    descricao = Column(Text)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Meta(Base):
    __tablename__ = "metas"
    
    id = Column(Integer, primary_key=True, index=True)
    setor = Column(String(100), nullable=False, index=True)
    kpi_nome = Column(String(255), nullable=False)
    periodo = Column(String(50), nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    valor_meta = Column(Float, nullable=False)
    valor_atual = Column(Float, default=0.0)
    status = Column(String(50), default="Em Andamento")
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    old_values = Column(Text)
    new_values = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
