"""Initial database schema

Revision ID: 4e61345a8f3d
Revises: 
Create Date: 2025-04-07 20:06:51.431948

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector import sqlalchemy

# revision identifiers, used by Alembic.
revision: str = '4e61345a8f3d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('projects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('logline', sa.Text(), nullable=True),
    sa.Column('global_synopsis', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_title'), 'projects', ['title'], unique=False)
    op.create_table('chapters',
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
    sa.UniqueConstraint('project_id', 'title', name='_project_chapter_title_uc')
    )
    op.create_index(op.f('ix_chapters_id'), 'chapters', ['id'], unique=False)
    op.create_table('characters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('backstory', sa.Text(), nullable=True),
    sa.Column('goals', sa.Text(), nullable=True),
    sa.Column('arc_summary', sa.Text(), nullable=True),
    sa.Column('current_status', sa.Text(), nullable=True),
    sa.Column('embedding', sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id', 'name', name='_project_character_name_uc')
    )
    op.create_index(op.f('ix_characters_id'), 'characters', ['id'], unique=False)
    op.create_index(op.f('ix_characters_name'), 'characters', ['name'], unique=False)
    op.create_table('setting_elements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('element_type', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('embedding', sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id', 'name', 'element_type', name='_project_setting_name_type_uc')
    )
    op.create_index(op.f('ix_setting_elements_element_type'), 'setting_elements', ['element_type'], unique=False)
    op.create_index(op.f('ix_setting_elements_id'), 'setting_elements', ['id'], unique=False)
    op.create_index(op.f('ix_setting_elements_name'), 'setting_elements', ['name'], unique=False)
    op.create_table('character_relationships',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('character1_id', sa.Integer(), nullable=False),
    sa.Column('character2_id', sa.Integer(), nullable=False),
    sa.Column('relationship_type', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('embedding', sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['character1_id'], ['characters.id'], ),
    sa.ForeignKeyConstraint(['character2_id'], ['characters.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('character1_id', 'character2_id', 'relationship_type', name='_character_relationship_uc')
    )
    op.create_index(op.f('ix_character_relationships_id'), 'character_relationships', ['id'], unique=False)
    op.create_table('scenes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('chapter_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('goal', sa.Text(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('generated_content', sa.Text(), nullable=True),
    sa.Column('order_in_chapter', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('PLANNED', 'DRAFTED', 'REVISING', 'COMPLETED', name='scenestatus'), nullable=False),
    sa.Column('goal_embedding', sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
    sa.Column('summary_embedding', sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenes_id'), 'scenes', ['id'], unique=False)
    op.create_table('scene_character_association',
    sa.Column('scene_id', sa.Integer(), nullable=False),
    sa.Column('character_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('scene_id', 'character_id')
    )
    op.create_table('scene_setting_association',
    sa.Column('scene_id', sa.Integer(), nullable=False),
    sa.Column('setting_element_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['setting_element_id'], ['setting_elements.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('scene_id', 'setting_element_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('scene_setting_association')
    op.drop_table('scene_character_association')
    op.drop_index(op.f('ix_scenes_id'), table_name='scenes')
    op.drop_table('scenes')
    op.drop_index(op.f('ix_character_relationships_id'), table_name='character_relationships')
    op.drop_table('character_relationships')
    op.drop_index(op.f('ix_setting_elements_name'), table_name='setting_elements')
    op.drop_index(op.f('ix_setting_elements_id'), table_name='setting_elements')
    op.drop_index(op.f('ix_setting_elements_element_type'), table_name='setting_elements')
    op.drop_table('setting_elements')
    op.drop_index(op.f('ix_characters_name'), table_name='characters')
    op.drop_index(op.f('ix_characters_id'), table_name='characters')
    op.drop_table('characters')
    op.drop_index(op.f('ix_chapters_id'), table_name='chapters')
    op.drop_table('chapters')
    op.drop_index(op.f('ix_projects_title'), table_name='projects')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
    # ### end Alembic commands ###
