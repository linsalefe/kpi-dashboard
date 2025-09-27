# backend/app/schemas.py
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, EmailStr, validator
from enum import Enum


# ================ ENUMS ================

class RoleEnum(str, Enum):
    """Roles do sistema - consistente com models.py"""
    FUNCIONARIO = "Funcionário"
    GESTOR = "Gestor"
    DIRETOR = "Diretor"


class SetorEnum(str, Enum):
    """Setores disponíveis"""
    MARKETING = "Marketing"
    COMERCIAL = "Comercial"
    EVENTOS = "Eventos"
    RH = "RH"
    PEDAGOGICO = "Pedagógico"
    FINANCEIRO = "Financeiro"


# ================ USER SCHEMAS ================

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Email do usuário")
    nome: str = Field(..., max_length=255, description="Nome completo")
    cargo: Optional[str] = Field(None, max_length=100, description="Cargo/função")
    setor: Optional[str] = Field(None, max_length=50, description="Setor de trabalho")
    role: RoleEnum = Field(RoleEnum.FUNCIONARIO, description="Nível de acesso")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Senha (mín. 6 caracteres)")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Email do usuário")
    nome: Optional[str] = Field(None, max_length=255, description="Nome completo")
    cargo: Optional[str] = Field(None, max_length=100, description="Cargo/função")
    setor: Optional[str] = Field(None, max_length=50, description="Setor de trabalho")
    role: Optional[RoleEnum] = Field(None, description="Nível de acesso")
    ativo: Optional[bool] = Field(None, description="Status ativo/inativo")


class UserResponse(UserBase):
    """Response com campos exatos do models.py"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    ativo: bool = True  # Campo 'ativo' como no models.py
    created_at: datetime
    updated_at: datetime
    # Campos opcionais que podem não existir ainda
    last_login: Optional[datetime] = None


# ================ MARKETING SCHEMAS ================

class MarketingDataBase(BaseModel):
    data_ref: date = Field(..., description="Data de referência do dado")
    canal: str = Field(..., max_length=50, description="Canal de marketing")
    campanha: str = Field(..., max_length=200, description="Nome da campanha")
    investimento: float = Field(..., ge=0, description="Valor investido (sem R$)")
    impressoes: int = Field(0, ge=0, description="Número de impressões")
    cliques: int = Field(0, ge=0, description="Número de cliques")
    conversoes: int = Field(0, ge=0, description="Número de conversões")
    leads: int = Field(0, ge=0, description="Leads gerados")
    vendas: int = Field(0, ge=0, description="Vendas realizadas")
    receita: float = Field(0.0, ge=0, description="Receita gerada (sem R$)")


class MarketingDataCreate(MarketingDataBase):
    pass


class MarketingDataUpdate(BaseModel):
    canal: Optional[str] = Field(None, max_length=50)
    campanha: Optional[str] = Field(None, max_length=200)
    investimento: Optional[float] = Field(None, ge=0)
    impressoes: Optional[int] = Field(None, ge=0)
    cliques: Optional[int] = Field(None, ge=0)
    conversoes: Optional[int] = Field(None, ge=0)
    leads: Optional[int] = Field(None, ge=0)
    vendas: Optional[int] = Field(None, ge=0)
    receita: Optional[float] = Field(None, ge=0)


class MarketingDataResponse(MarketingDataBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# ================ COMERCIAL SCHEMAS ================

class ComercialDataBase(BaseModel):
    data_ref: date = Field(..., description="Data de referência")
    vendedor: str = Field(..., max_length=100, description="Nome do vendedor")
    produto: str = Field(..., max_length=200, description="Nome do produto")
    categoria: Optional[str] = Field(None, max_length=100, description="Categoria do produto")
    leads_recebidos: int = Field(0, ge=0, description="Leads recebidos")
    contatos_realizados: int = Field(0, ge=0, description="Contatos realizados")
    propostas_enviadas: int = Field(0, ge=0, description="Propostas enviadas")
    vendas_fechadas: int = Field(0, ge=0, description="Vendas fechadas")
    valor_vendas: float = Field(0.0, ge=0, description="Valor total de vendas")
    ticket_medio: float = Field(0.0, ge=0, description="Ticket médio")


class ComercialDataCreate(ComercialDataBase):
    pass


class ComercialDataUpdate(BaseModel):
    vendedor: Optional[str] = Field(None, max_length=100)
    produto: Optional[str] = Field(None, max_length=200)
    categoria: Optional[str] = Field(None, max_length=100)
    leads_recebidos: Optional[int] = Field(None, ge=0)
    contatos_realizados: Optional[int] = Field(None, ge=0)
    propostas_enviadas: Optional[int] = Field(None, ge=0)
    vendas_fechadas: Optional[int] = Field(None, ge=0)
    valor_vendas: Optional[float] = Field(None, ge=0)
    ticket_medio: Optional[float] = Field(None, ge=0)


class ComercialDataResponse(ComercialDataBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# ================ EVENTOS SCHEMAS ================

class EventosDataBase(BaseModel):
    data_ref: date = Field(..., description="Data de referência")
    evento: str = Field(..., max_length=200, description="Nome do evento")
    tipo_evento: Optional[str] = Field(None, max_length=100, description="Tipo do evento")
    modalidade: Optional[str] = Field(None, max_length=50, description="Online/Presencial/Híbrido")
    inscricoes: int = Field(0, ge=0, description="Número de inscrições")
    participantes: int = Field(0, ge=0, description="Número de participantes")
    no_shows: int = Field(0, ge=0, description="Número de no-shows")
    leads_gerados: int = Field(0, ge=0, description="Leads gerados")
    custo_evento: float = Field(0.0, ge=0, description="Custo do evento")
    receita_evento: float = Field(0.0, ge=0, description="Receita do evento")


class EventosDataCreate(EventosDataBase):
    pass


class EventosDataUpdate(BaseModel):
    evento: Optional[str] = Field(None, max_length=200)
    tipo_evento: Optional[str] = Field(None, max_length=100)
    modalidade: Optional[str] = Field(None, max_length=50)
    inscricoes: Optional[int] = Field(None, ge=0)
    participantes: Optional[int] = Field(None, ge=0)
    no_shows: Optional[int] = Field(None, ge=0)
    leads_gerados: Optional[int] = Field(None, ge=0)
    custo_evento: Optional[float] = Field(None, ge=0)
    receita_evento: Optional[float] = Field(None, ge=0)


class EventosDataResponse(EventosDataBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# ================ RH SCHEMAS ================

class RhDataBase(BaseModel):
    """Usando 'Rh' para coincidir com a tabela 'rh_data' do models.py"""
    data_ref: date = Field(..., description="Data de referência")
    departamento: str = Field(..., max_length=100, description="Nome do departamento")
    funcionarios_ativos: int = Field(0, ge=0, description="Funcionários ativos")
    novas_contratacoes: int = Field(0, ge=0, description="Novas contratações")
    desligamentos: int = Field(0, ge=0, description="Desligamentos")
    faltas: int = Field(0, ge=0, description="Número de faltas")
    horas_extras: float = Field(0.0, ge=0, description="Horas extras")
    treinamentos_realizados: int = Field(0, ge=0, description="Treinamentos realizados")
    participantes_treinamento: int = Field(0, ge=0, description="Participantes em treinamento")
    custo_folha: float = Field(0.0, ge=0, description="Custo da folha de pagamento")


class RhDataCreate(RhDataBase):
    pass


class RhDataUpdate(BaseModel):
    departamento: Optional[str] = Field(None, max_length=100)
    funcionarios_ativos: Optional[int] = Field(None, ge=0)
    novas_contratacoes: Optional[int] = Field(None, ge=0)
    desligamentos: Optional[int] = Field(None, ge=0)
    faltas: Optional[int] = Field(None, ge=0)
    horas_extras: Optional[float] = Field(None, ge=0)
    treinamentos_realizados: Optional[int] = Field(None, ge=0)
    participantes_treinamento: Optional[int] = Field(None, ge=0)
    custo_folha: Optional[float] = Field(None, ge=0)


class RhDataResponse(RhDataBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# ================ PEDAGÓGICO SCHEMAS ================

class PedagogicoDataBase(BaseModel):
    data_ref: date = Field(..., description="Data de referência")
    curso: str = Field(..., max_length=200, description="Nome do curso")
    modalidade: Optional[str] = Field(None, max_length=50, description="Online/Presencial/Híbrido")
    turma: Optional[str] = Field(None, max_length=100, description="Código da turma")
    alunos_matriculados: int = Field(0, ge=0, description="Alunos matriculados")
    alunos_ativos: int = Field(0, ge=0, description="Alunos ativos")
    evasao: int = Field(0, ge=0, description="Número de evasões")
    conclusoes: int = Field(0, ge=0, description="Número de conclusões")
    nota_media: float = Field(0.0, ge=0, le=10, description="Nota média (0-10)")
    satisfacao: float = Field(0.0, ge=0, le=10, description="Satisfação (0-10)")


class PedagogicoDataCreate(PedagogicoDataBase):
    pass


class PedagogicoDataUpdate(BaseModel):
    curso: Optional[str] = Field(None, max_length=200)
    modalidade: Optional[str] = Field(None, max_length=50)
    turma: Optional[str] = Field(None, max_length=100)
    alunos_matriculados: Optional[int] = Field(None, ge=0)
    alunos_ativos: Optional[int] = Field(None, ge=0)
    evasao: Optional[int] = Field(None, ge=0)
    conclusoes: Optional[int] = Field(None, ge=0)
    nota_media: Optional[float] = Field(None, ge=0, le=10)
    satisfacao: Optional[float] = Field(None, ge=0, le=10)


class PedagogicoDataResponse(PedagogicoDataBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# ================ FINANCEIRO SCHEMAS ================

class FinanceiroDataBase(BaseModel):
    data_ref: date = Field(..., description="Data de referência")
    categoria: str = Field(..., max_length=100, description="Categoria financeira")
    subcategoria: Optional[str] = Field(None, max_length=100, description="Subcategoria")
    centro_custo: Optional[str] = Field(None, max_length=100, description="Centro de custo")
    receitas: float = Field(0.0, description="Receitas (pode ser negativo para estorno)")
    despesas: float = Field(0.0, ge=0, description="Despesas")
    contas_receber: float = Field(0.0, ge=0, description="Contas a receber")
    contas_pagar: float = Field(0.0, ge=0, description="Contas a pagar")
    inadimplencia: float = Field(0.0, ge=0, description="Valor em inadimplência")


class FinanceiroDataCreate(FinanceiroDataBase):
    pass


class FinanceiroDataUpdate(BaseModel):
    categoria: Optional[str] = Field(None, max_length=100)
    subcategoria: Optional[str] = Field(None, max_length=100)
    centro_custo: Optional[str] = Field(None, max_length=100)
    receitas: Optional[float] = Field(None)
    despesas: Optional[float] = Field(None, ge=0)
    contas_receber: Optional[float] = Field(None, ge=0)
    contas_pagar: Optional[float] = Field(None, ge=0)
    inadimplencia: Optional[float] = Field(None, ge=0)


class FinanceiroDataResponse(FinanceiroDataBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# ================ METAS SCHEMAS ================

class MetasBase(BaseModel):
    setor: str = Field(..., max_length=50, description="Setor da meta")
    kpi_nome: str = Field(..., max_length=100, description="Nome do KPI")
    periodo: str = Field(..., max_length=20, description="Período (diario/semanal/mensal/anual)")
    valor_meta: float = Field(..., description="Valor da meta")
    unidade: Optional[str] = Field(None, max_length=20, description="Unidade (%, R$, unidades)")
    data_inicio: date = Field(..., description="Data de início")
    data_fim: date = Field(..., description="Data de fim")
    ativo: bool = Field(True, description="Meta ativa")


class MetasCreate(MetasBase):
    @validator('data_fim')
    def validate_data_fim(cls, v, values):
        if 'data_inicio' in values and v <= values['data_inicio']:
            raise ValueError('data_fim deve ser posterior a data_inicio')
        return v


class MetasUpdate(BaseModel):
    setor: Optional[str] = Field(None, max_length=50)
    kpi_nome: Optional[str] = Field(None, max_length=100)
    periodo: Optional[str] = Field(None, max_length=20)
    valor_meta: Optional[float] = Field(None)
    unidade: Optional[str] = Field(None, max_length=20)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    ativo: Optional[bool] = None


class MetasResponse(MetasBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# ================ AUDIT LOG SCHEMAS ================

class AuditLogBase(BaseModel):
    acao: str = Field(..., max_length=50, description="Ação realizada")
    tabela: Optional[str] = Field(None, max_length=50, description="Tabela afetada")
    registro_id: Optional[int] = Field(None, description="ID do registro afetado")
    dados_antes: Optional[str] = Field(None, description="Dados antes da alteração (JSON)")
    dados_depois: Optional[str] = Field(None, description="Dados depois da alteração (JSON)")
    ip_address: Optional[str] = Field(None, max_length=45, description="Endereço IP")
    user_agent: Optional[str] = Field(None, description="User Agent do navegador")


class AuditLogCreate(AuditLogBase):
    user_id: int = Field(..., description="ID do usuário que realizou a ação")


class AuditLogResponse(AuditLogBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    timestamp: datetime


# ================ RESPONSE MODELS GERAIS ================

class SuccessResponse(BaseModel):
    status: str = "success"
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    details: Optional[dict] = None


class PaginatedResponse(BaseModel):
    status: str = "success"
    total: int
    page: int = 1
    per_page: int = 50
    data: List[dict]


class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"
    database: str = "connected"


# ================ SCHEMAS DE FILTRO ================

class FilterBase(BaseModel):
    """Base para filtros de consulta"""
    data_inicio: Optional[date] = Field(None, description="Data de início do filtro")
    data_fim: Optional[date] = Field(None, description="Data de fim do filtro")
    page: int = Field(1, ge=1, description="Página")
    per_page: int = Field(50, ge=1, le=100, description="Items por página")


class MarketingFilter(FilterBase):
    canal: Optional[str] = Field(None, description="Filtrar por canal")
    campanha: Optional[str] = Field(None, description="Filtrar por campanha")


class ComercialFilter(FilterBase):
    vendedor: Optional[str] = Field(None, description="Filtrar por vendedor")
    produto: Optional[str] = Field(None, description="Filtrar por produto")
    categoria: Optional[str] = Field(None, description="Filtrar por categoria")


class EventosFilter(FilterBase):
    tipo_evento: Optional[str] = Field(None, description="Filtrar por tipo de evento")
    modalidade: Optional[str] = Field(None, description="Filtrar por modalidade")


class RhFilter(FilterBase):
    departamento: Optional[str] = Field(None, description="Filtrar por departamento")


class PedagogicoFilter(FilterBase):
    curso: Optional[str] = Field(None, description="Filtrar por curso")
    modalidade: Optional[str] = Field(None, description="Filtrar por modalidade")


class FinanceiroFilter(FilterBase):
    categoria: Optional[str] = Field(None, description="Filtrar por categoria")
    subcategoria: Optional[str] = Field(None, description="Filtrar por subcategoria")
    centro_custo: Optional[str] = Field(None, description="Filtrar por centro de custo")