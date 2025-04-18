"""增加卷

Revision ID: cb9f60967868
Revises: 99901c51854f
Create Date: 2025-04-10 22:19:38.860618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector import sqlalchemy

# revision identifiers, used by Alembic.
revision: str = 'cb9f60967868'
down_revision: Union[str, None] = '99901c51854f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('volumes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('embedding', sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id', 'title', name='_project_volume_title_uc')
    )
    op.create_index(op.f('ix_volumes_id'), 'volumes', ['id'], unique=False)
    op.add_column('chapters', sa.Column('volume_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'chapters', 'volumes', ['volume_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'chapters', type_='foreignkey')
    op.drop_column('chapters', 'volume_id')
    op.drop_index(op.f('ix_volumes_id'), table_name='volumes')
    op.drop_table('volumes')
    # ### end Alembic commands ###
