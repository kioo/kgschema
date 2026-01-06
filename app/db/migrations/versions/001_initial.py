"""Initial schema creation

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(64), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('role', sa.String(32), nullable=False, server_default='USER'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_users_username', 'users', ['username'])

    # Entities table
    op.create_table(
        'entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_code', sa.String(128), nullable=False, unique=True),
        sa.Column('entity_name', sa.String(256), nullable=False),
        sa.Column('entity_name_en', sa.String(256)),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(16), nullable=False, server_default='DRAFT'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_entities_entity_code', 'entities', ['entity_code'])
    op.create_index('ix_entities_status', 'entities', ['status'])
    op.create_index('ix_entities_is_active', 'entities', ['is_active'])

    # Entity properties table
    op.create_table(
        'entity_properties',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prop_code', sa.String(128), nullable=False),
        sa.Column('prop_name', sa.String(256), nullable=False),
        sa.Column('prop_name_en', sa.String(256)),
        sa.Column('data_type', sa.String(32), nullable=False, server_default='STRING'),
        sa.Column('options_json', postgresql.JSONB()),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('entity_id', 'prop_code', name='uq_entity_properties_entity_id_prop_code'),
    )
    op.create_index('ix_entity_properties_entity_id', 'entity_properties', ['entity_id'])

    # Relations table
    op.create_table(
        'relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('relation_code', sa.String(128), nullable=False, unique=True),
        sa.Column('relation_name', sa.String(256), nullable=False),
        sa.Column('relation_name_en', sa.String(256)),
        sa.Column('head_entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id'), nullable=False),
        sa.Column('tail_entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id'), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(16), nullable=False, server_default='DRAFT'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_relations_relation_code', 'relations', ['relation_code'])
    op.create_index('ix_relations_status', 'relations', ['status'])
    op.create_index('ix_relations_head_entity_id', 'relations', ['head_entity_id'])
    op.create_index('ix_relations_tail_entity_id', 'relations', ['tail_entity_id'])

    # Relation properties table
    op.create_table(
        'relation_properties',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('relation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('relations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prop_code', sa.String(128), nullable=False),
        sa.Column('prop_name', sa.String(256), nullable=False),
        sa.Column('prop_name_en', sa.String(256)),
        sa.Column('data_type', sa.String(32), nullable=False, server_default='STRING'),
        sa.Column('options_json', postgresql.JSONB()),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('relation_id', 'prop_code', name='uq_relation_properties_relation_id_prop_code'),
    )
    op.create_index('ix_relation_properties_relation_id', 'relation_properties', ['relation_id'])

    # Schema versions table
    op.create_table(
        'schema_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('version', sa.Integer(), nullable=False, unique=True),
        sa.Column('snapshot_jsonb', postgresql.JSONB(), nullable=False),
        sa.Column('release_notes', sa.Text()),
        sa.Column('published_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_schema_versions_version', 'schema_versions', ['version'], postgresql_using='btree')

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True)),
        sa.Column('module', sa.String(64), nullable=False),
        sa.Column('action', sa.String(32), nullable=False),
        sa.Column('object_type', sa.String(64), nullable=False),
        sa.Column('object_id', postgresql.UUID(as_uuid=True)),
        sa.Column('before_jsonb', postgresql.JSONB()),
        sa.Column('after_jsonb', postgresql.JSONB()),
        sa.Column('operator_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_module', 'audit_logs', ['module'])
    op.create_index('ix_audit_logs_operator_id', 'audit_logs', ['operator_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_batch_id', 'audit_logs', ['batch_id'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('schema_versions')
    op.drop_table('relation_properties')
    op.drop_table('relations')
    op.drop_table('entity_properties')
    op.drop_table('entities')
    op.drop_table('users')
