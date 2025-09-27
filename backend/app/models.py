from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone

Base = declarative_base()

# Timezone para América/Fortaleza
TIMEZONE = "America/Fortaleza"

class User(Base):
    """Usuários do sistema"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    nome = Column(String(255), nullable=False)
    cargo = Column(String(100))
    setor = Column(String(50))  # Marketing, Comercial, Eventos, RH, Pedagógico, Financeiro
    role = Column(String(20), default="Funcionário")  # Funcionário, Gestor, Diretor
    password_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class MarketingData(Base):
    """Dados brutos de Marketing"""
    __tablename__ = "marketing_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False, comment="Data de referência do dado")
    canal = Column(String(50), nullable=False)  # Facebook, Google, Instagram, etc.
    campanha = Column(String(200), nullable=False)
    investimento = Column(Float, nullable=False, comment="Valor sem símbolo R$")
    impressoes = Column(Integer, default=0)
    cliques = Column(Integer, default=0)
    conversoes = Column(Integer, default=0)
    leads = Column(Integer, default=0)
    vendas = Column(Integer, default=0)
    receita = Column(Float, default=0.0, comment="Valor sem símbolo R$")
    
    # Metadados
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    user = relationship("User")
    
    # Índices compostos para anti-duplicidade
    __table_args__ = (
        Index('idx_marketing_unique', 'data_ref', 'canal', 'campanha'),
    )

class ComercialData(Base):
    """Dados brutos do Comercial"""
    __tablename__ = "comercial_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False)
    vendedor = Column(String(100), nullable=False)
    produto = Column(String(200), nullable=False)
    categoria = Column(String(100))
    leads_recebidos = Column(Integer, default=0)
    contatos_realizados = Column(Integer, default=0)
    propostas_enviadas = Column(Integer, default=0)
    vendas_fechadas = Column(Integer, default=0)
    valor_vendas = Column(Float, default=0.0)
    ticket_medio = Column(Float, default=0.0)
    
    # Metadados
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_comercial_unique', 'data_ref', 'vendedor', 'produto'),
    )

class EventosData(Base):
    """Dados brutos de Eventos"""
    __tablename__ = "eventos_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False)
    evento = Column(String(200), nullable=False)
    tipo_evento = Column(String(100))  # Webinar, Workshop, Palestra, etc.
    modalidade = Column(String(50))    # Online, Presencial, Híbrido
    inscricoes = Column(Integer, default=0)
    participantes = Column(Integer, default=0)
    no_shows = Column(Integer, default=0)
    leads_gerados = Column(Integer, default=0)
    custo_evento = Column(Float, default=0.0)
    receita_evento = Column(Float, default=0.0)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_eventos_unique', 'data_ref', 'evento'),
    )

class RhData(Base):
    """Dados brutos de RH"""
    __tablename__ = "rh_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False)
    departamento = Column(String(100), nullable=False)
    funcionarios_ativos = Column(Integer, default=0)
    novas_contratacoes = Column(Integer, default=0)
    desligamentos = Column(Integer, default=0)
    faltas = Column(Integer, default=0)
    horas_extras = Column(Float, default=0.0)
    treinamentos_realizados = Column(Integer, default=0)
    participantes_treinamento = Column(Integer, default=0)
    custo_folha = Column(Float, default=0.0)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_rh_unique', 'data_ref', 'departamento'),
    )

class PedagogicoData(Base):
    """Dados brutos do Pedagógico"""
    __tablename__ = "pedagogico_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False)
    curso = Column(String(200), nullable=False)
    modalidade = Column(String(50))    # Online, Presencial, Híbrido
    turma = Column(String(100))
    alunos_matriculados = Column(Integer, default=0)
    alunos_ativos = Column(Integer, default=0)
    evasao = Column(Integer, default=0)
    conclusoes = Column(Integer, default=0)
    nota_media = Column(Float, default=0.0)
    satisfacao = Column(Float, default=0.0)  # Nota de 0 a 10
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_pedagogico_unique', 'data_ref', 'curso', 'turma'),
    )

class FinanceiroData(Base):
    """Dados brutos do Financeiro"""
    __tablename__ = "financeiro_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_ref = Column(Date, nullable=False)
    categoria = Column(String(100), nullable=False)  # Receita, Despesa
    subcategoria = Column(String(100))
    centro_custo = Column(String(100))
    receitas = Column(Float, default=0.0)
    despesas = Column(Float, default=0.0)
    contas_receber = Column(Float, default=0.0)
    contas_pagar = Column(Float, default=0.0)
    inadimplencia = Column(Float, default=0.0)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_financeiro_unique', 'data_ref', 'categoria', 'subcategoria'),
    )

class Metas(Base):
    """Metas centralizadas por setor e período"""
    __tablename__ = "metas"
    
    id = Column(Integer, primary_key=True, index=True)
    setor = Column(String(50), nullable=False)
    kpi_nome = Column(String(100), nullable=False)
    periodo = Column(String(20), nullable=False)  # diario, semanal, mensal, anual
    valor_meta = Column(Float, nullable=False)
    unidade = Column(String(20))  # %, R$, unidades, etc.
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    ativo = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AuditLog(Base):
    """Log de auditoria - quem/quando/o que"""
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    acao = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN
    tabela = Column(String(50))
    registro_id = Column(Integer)
    dados_antes = Column(Text)  # JSON dos dados antes da alteração
    dados_depois = Column(Text)  # JSON dos dados após a alteração
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
    
    # Índices para consultas de auditoria
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_tabela_timestamp', 'tabela', 'timestamp'),
    )