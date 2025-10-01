"""add_produto_to_marketing_data

Revision ID: 128f98cf51ca
Revises: 29efaef05c8d
Create Date: 2025-10-01 09:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '128f98cf51ca'
down_revision: Union[str, None] = '29efaef05c8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adicionar coluna produto (temporariamente NULL)
    op.add_column('marketing_data', sa.Column('produto', sa.String(length=50), nullable=True))
    
    # Popular registros existentes com valor padrão
    op.execute("UPDATE marketing_data SET produto = 'Não especificado' WHERE produto IS NULL")
    
    # Tornar a coluna NOT NULL
    op.alter_column('marketing_data', 'produto', nullable=False)
    
    # Criar índice
    op.create_index('ix_marketing_data_produto', 'marketing_data', ['produto'], unique=False)


def downgrade() -> None:
    # Remover índice
    op.drop_index('ix_marketing_data_produto', table_name='marketing_data')
    
    # Remover coluna
    op.drop_column('marketing_data', 'produto')
