from pydantic import BaseModel, EmailStr, Field, validator
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


# ============= ENUMS =============

class UserRole(str, Enum):
    FUNCIONARIO = "Funcionário"
    GESTOR = "Gestor"
    DIRETOR = "Diretor"


class ProdutoMarketing(str, Enum):
    CONGRESSOS = "Congressos"
    POS_GRADUACOES = "Pós-Graduações"
    CURSOS_HOTMART = "Cursos Hotmart"
    SEMINARIO = "Seminário"
    INTERCAMBIOS = "Intercâmbios"


# ============= USER SCHEMAS =============

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.FUNCIONARIO


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# ============= MARKETING SCHEMAS =============

class MarketingBase(BaseModel):
    data_ref: date
    produto: ProdutoMarketing
    canal: str = Field(..., min_length=1, max_length=100)
    campanha: str = Field(..., min_length=1, max_length=255)
    investimento: float = Field(..., ge=0)
    impressoes: int = Field(default=0, ge=0)
    cliques: int = Field(default=0, ge=0)
    leads: int = Field(default=0, ge=0)
    vendas: int = Field(default=0, ge=0)
    receita: float = Field(default=0.0, ge=0)
    
    @validator('investimento', 'receita')
    def round_currency(cls, v):
        return round(v, 2)


class MarketingCreate(MarketingBase):
    pass


class MarketingUpdate(BaseModel):
    data_ref: Optional[date] = None
    produto: Optional[ProdutoMarketing] = None
    canal: Optional[str] = Field(None, min_length=1, max_length=100)
    campanha: Optional[str] = Field(None, min_length=1, max_length=255)
    investimento: Optional[float] = Field(None, ge=0)
    impressoes: Optional[int] = Field(None, ge=0)
    cliques: Optional[int] = Field(None, ge=0)
    leads: Optional[int] = Field(None, ge=0)
    vendas: Optional[int] = Field(None, ge=0)
    receita: Optional[float] = Field(None, ge=0)
    
    @validator('investimento', 'receita')
    def round_currency(cls, v):
        if v is not None:
            return round(v, 2)
        return v


class MarketingResponse(MarketingBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= COMERCIAL SCHEMAS =============

class ComercialBase(BaseModel):
    data_ref: date
    vendedor: str = Field(..., min_length=1, max_length=255)
    produto: str = Field(..., min_length=1, max_length=255)
    quantidade: int = Field(default=0, ge=0)
    valor_total: float = Field(default=0.0, ge=0)
    comissao: float = Field(default=0.0, ge=0)
    
    @validator('valor_total', 'comissao')
    def round_currency(cls, v):
        return round(v, 2)


class ComercialCreate(ComercialBase):
    pass


class ComercialResponse(ComercialBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= EVENTOS SCHEMAS =============

class EventosBase(BaseModel):
    data_ref: date
    nome_evento: str = Field(..., min_length=1, max_length=255)
    tipo_evento: str = Field(..., min_length=1, max_length=100)
    participantes: int = Field(default=0, ge=0)
    custo_total: float = Field(default=0.0, ge=0)
    receita: float = Field(default=0.0, ge=0)
    
    @validator('custo_total', 'receita')
    def round_currency(cls, v):
        return round(v, 2)


class EventosCreate(EventosBase):
    pass


class EventosResponse(EventosBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= RH SCHEMAS =============

class RHBase(BaseModel):
    data_ref: date
    departamento: str = Field(..., min_length=1, max_length=100)
    total_funcionarios: int = Field(default=0, ge=0)
    admissoes: int = Field(default=0, ge=0)
    demissoes: int = Field(default=0, ge=0)
    horas_treinamento: float = Field(default=0.0, ge=0)
    custo_total: float = Field(default=0.0, ge=0)
    
    @validator('custo_total')
    def round_currency(cls, v):
        return round(v, 2)


class RHCreate(RHBase):
    pass


class RHResponse(RHBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= PEDAGÓGICO SCHEMAS =============

class PedagogicoBase(BaseModel):
    data_ref: date
    curso: str = Field(..., min_length=1, max_length=255)
    turma: str = Field(..., min_length=1, max_length=100)
    alunos_matriculados: int = Field(default=0, ge=0)
    frequencia_media: float = Field(default=0.0, ge=0, le=100)
    nota_media: float = Field(default=0.0, ge=0, le=10)
    evasao: int = Field(default=0, ge=0)


class PedagogicoCreate(PedagogicoBase):
    pass


class PedagogicoResponse(PedagogicoBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= FINANCEIRO SCHEMAS =============

class FinanceiroBase(BaseModel):
    data_ref: date
    categoria: str = Field(..., min_length=1, max_length=100)
    tipo: str = Field(..., pattern="^(Receita|Despesa)$")
    valor: float = Field(..., ge=0)
    descricao: Optional[str] = None
    
    @validator('valor')
    def round_currency(cls, v):
        return round(v, 2)


class FinanceiroCreate(FinanceiroBase):
    pass


class FinanceiroResponse(FinanceiroBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= META SCHEMAS =============

class MetaBase(BaseModel):
    setor: str = Field(..., min_length=1, max_length=100)
    kpi_nome: str = Field(..., min_length=1, max_length=255)
    periodo: str = Field(..., pattern="^(mensal|trimestral|anual)$")
    data_inicio: date
    data_fim: date
    valor_meta: float
    valor_atual: float = 0.0
    status: str = Field(default="Em Andamento")


class MetaCreate(MetaBase):
    pass


class MetaResponse(MetaBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Alias para compatibilidade com código existente
RoleEnum = UserRole
