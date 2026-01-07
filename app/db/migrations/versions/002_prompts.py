"""Add prompts and prompt_versions tables

Revision ID: 002_prompts
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002_prompts'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Prompts table
    op.create_table(
        'prompts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tag', sa.String(128), nullable=False, unique=True, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('current_version', sa.Integer(), nullable=False, default=1),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Prompt versions table
    op.create_table(
        'prompt_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('prompt_id', sa.String(36), sa.ForeignKey('prompts.id'), nullable=False, index=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('change_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create unique constraint for prompt_id + version
    op.create_index('ix_prompt_versions_prompt_version', 'prompt_versions', ['prompt_id', 'version'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_prompt_versions_prompt_version', 'prompt_versions')
    op.drop_table('prompt_versions')
    op.drop_table('prompts')
