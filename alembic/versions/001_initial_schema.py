"""Initial schema for anchors and anchor_events

Revision ID: 001
Revises: 
Create Date: 2024-12-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Anchors table
    op.create_table(
        'anchors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('anchor_id', sa.String(64), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('hardware_model', sa.String(128), nullable=False),
        sa.Column('firmware_version', sa.String(32), nullable=False),
        sa.Column('manufacturer_id', sa.String(64), nullable=False),
        sa.Column('public_key', sa.String(128), nullable=False),
        sa.Column('status', sa.Enum('active', 'sealed', 'breached', 'inactive', name='anchorstatus'), nullable=False),
        sa.Column('certification_tier', sa.Enum('compatible', 'native', 'verified', name='certificationtier'), nullable=False),
        sa.Column('current_seal_id', sa.String(64), nullable=True),
        sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_event_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=True, default=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.String(256), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_anchors_anchor_id', 'anchors', ['anchor_id'], unique=True)
    op.create_index('ix_anchors_asset_id', 'anchors', ['asset_id'])
    op.create_index('ix_anchors_manufacturer_id', 'anchors', ['manufacturer_id'])

    # Anchor events table
    op.create_table(
        'anchor_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.Enum(
            'ANCHOR_REGISTERED', 'ANCHOR_SEAL_ARMED', 'ANCHOR_SEAL_BROKEN',
            'ANCHOR_ENVIRONMENTAL_ALERT', 'ANCHOR_CUSTODY_SIGNAL',
            name='anchoreventtype'
        ), nullable=False),
        sa.Column('anchor_id', sa.String(64), nullable=False),
        sa.Column('schema_version', sa.String(16), nullable=False),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('signature', sa.Text(), nullable=False),
        sa.Column('signature_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('seal_id', sa.String(64), nullable=True),
        sa.Column('geo_lat_e7', sa.Integer(), nullable=True),
        sa.Column('geo_lon_e7', sa.Integer(), nullable=True),
        sa.Column('trigger_type', sa.Enum('MANUAL', 'FORCE', 'TAMPER', 'UNKNOWN', name='triggertype'), nullable=True),
        sa.Column('metric', sa.Enum('SHOCK', 'TEMP', 'HUMIDITY', name='environmentalmetric'), nullable=True),
        sa.Column('metric_value', sa.String(64), nullable=True),
        sa.Column('metric_threshold', sa.String(64), nullable=True),
        sa.Column('challenge_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('custody_direction', sa.Enum('RELEASE', 'ACCEPT', name='custodydirection'), nullable=True),
        sa.Column('counterparty_pubkey', sa.String(128), nullable=True),
        sa.Column('hardware_model', sa.String(128), nullable=True),
        sa.Column('firmware_version', sa.String(32), nullable=True),
        sa.Column('manufacturer_id', sa.String(64), nullable=True),
        sa.Column('raw_payload', postgresql.JSON(), nullable=False),
        sa.Column('ledger_synced', sa.Boolean(), nullable=True, default=False),
        sa.Column('ledger_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ledger_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=True, default=False),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_anchor_events_event_type', 'anchor_events', ['event_type'])
    op.create_index('ix_anchor_events_anchor_id', 'anchor_events', ['anchor_id'])
    op.create_index('ix_anchor_events_event_timestamp', 'anchor_events', ['event_timestamp'])


def downgrade() -> None:
    op.drop_index('ix_anchor_events_event_timestamp', table_name='anchor_events')
    op.drop_index('ix_anchor_events_anchor_id', table_name='anchor_events')
    op.drop_index('ix_anchor_events_event_type', table_name='anchor_events')
    op.drop_table('anchor_events')
    
    op.drop_index('ix_anchors_manufacturer_id', table_name='anchors')
    op.drop_index('ix_anchors_asset_id', table_name='anchors')
    op.drop_index('ix_anchors_anchor_id', table_name='anchors')
    op.drop_table('anchors')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS custodydirection')
    op.execute('DROP TYPE IF EXISTS environmentalmetric')
    op.execute('DROP TYPE IF EXISTS triggertype')
    op.execute('DROP TYPE IF EXISTS anchoreventtype')
    op.execute('DROP TYPE IF EXISTS certificationtier')
    op.execute('DROP TYPE IF EXISTS anchorstatus')
