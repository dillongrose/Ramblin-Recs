"""init tables with pgvector"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'users',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.Text(), nullable=False, unique=True),
        sa.Column('display_name', sa.Text(), nullable=True),
        sa.Column('interests', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('embed', Vector(384), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'))
    )

    op.create_table(
        'events',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('end_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('timezone', sa.Text(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('host', sa.Text(), nullable=True),
        sa.Column('price_cents', sa.Integer(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('tags', sa.dialects.postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('raw_s3_uri', sa.Text(), nullable=True),
        sa.Column('embed', Vector(384), nullable=True),
        sa.Column('popularity', sa.Float(), server_default=sa.text('0')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'))
    )

    op.create_table(
    'feedback',
    sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),  # ✅ new PK
    sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True),
              sa.ForeignKey('users.id', ondelete="CASCADE"), nullable=False),
    sa.Column('event_id', sa.dialects.postgresql.UUID(as_uuid=True),
              sa.ForeignKey('events.id', ondelete="CASCADE"), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
    sa.Column('clicked', sa.Boolean(), server_default=sa.text('false')),
    sa.Column('saved', sa.Boolean(), server_default=sa.text('false')),
    sa.Column('rsvp', sa.Boolean(), server_default=sa.text('false')),
    sa.Column('dwell_seconds', sa.Integer(), server_default=sa.text('0'))
    )
    # helpful indexes
    op.create_index('ix_feedback_user', 'feedback', ['user_id'])
    op.create_index('ix_feedback_event', 'feedback', ['event_id'])
    op.create_index('ix_feedback_created_at', 'feedback', ['created_at'])


    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_events_embed "
        "ON events USING ivfflat (embed vector_cosine_ops) WITH (lists = 100)"
    )

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_events_embed")
    op.drop_table('feedback')
    op.drop_table('events')
    op.drop_table('users')
