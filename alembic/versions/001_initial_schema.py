"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-12-24

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create source_content table
    op.create_table(
        'source_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_url', sa.String(), nullable=False),
        sa.Column('video_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('audio_path', sa.String(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='contentstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_content_id'), 'source_content', ['id'], unique=False)
    op.create_index(op.f('ix_source_content_video_url'), 'source_content', ['video_url'], unique=True)
    op.create_index(op.f('ix_source_content_video_id'), 'source_content', ['video_id'], unique=True)
    
    # Create style_guide table
    op.create_table(
        'style_guide',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('rules', sa.Text(), nullable=False),
        sa.Column('examples', sa.JSON(), nullable=True),
        sa.Column('tone', sa.String(), nullable=True),
        sa.Column('voice_description', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_style_guide_id'), 'style_guide', ['id'], unique=False)
    op.create_index(op.f('ix_style_guide_name'), 'style_guide', ['name'], unique=True)
    
    # Create generated_content table
    op.create_table(
        'generated_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('TWITTER', 'LINKEDIN', 'INSTAGRAM', 'NEWSLETTER', name='platform'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_parts', sa.Text(), nullable=True),
        sa.Column('media_urls', sa.Text(), nullable=True),
        sa.Column('approval_status', sa.Enum('PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'PUBLISHED', 'FAILED', name='approvalstatus'), nullable=False),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_url', sa.String(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['source_content.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generated_content_id'), 'generated_content', ['id'], unique=False)
    op.create_index(op.f('ix_generated_content_source_id'), 'generated_content', ['source_id'], unique=False)
    op.create_index(op.f('ix_generated_content_platform'), 'generated_content', ['platform'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_generated_content_platform'), table_name='generated_content')
    op.drop_index(op.f('ix_generated_content_source_id'), table_name='generated_content')
    op.drop_index(op.f('ix_generated_content_id'), table_name='generated_content')
    op.drop_table('generated_content')
    op.drop_index(op.f('ix_style_guide_name'), table_name='style_guide')
    op.drop_index(op.f('ix_style_guide_id'), table_name='style_guide')
    op.drop_table('style_guide')
    op.drop_index(op.f('ix_source_content_video_id'), table_name='source_content')
    op.drop_index(op.f('ix_source_content_video_url'), table_name='source_content')
    op.drop_index(op.f('ix_source_content_id'), table_name='source_content')
    op.drop_table('source_content')
    op.execute('DROP EXTENSION IF EXISTS vector')
