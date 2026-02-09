"""manual_add_fields

Revision ID: b9f265640762
Revises: a8e154539651
Create Date: 2026-02-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'b9f265640762'
down_revision = 'a8e154539651'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Products
    columns = [c['name'] for c in inspector.get_columns('products')]
    if 'is_hit' not in columns:
        op.add_column('products', sa.Column('is_hit', sa.Boolean(), nullable=True, server_default='false'))
    if 'is_discount' not in columns:
        op.add_column('products', sa.Column('is_discount', sa.Boolean(), nullable=True, server_default='false'))
    if 'image_url' not in columns:
        op.add_column('products', sa.Column('image_url', sa.String(), nullable=True))
        
    # Categories
    cat_columns = [c['name'] for c in inspector.get_columns('categories')]
    if 'image_url' not in cat_columns:
        op.add_column('categories', sa.Column('image_url', sa.String(), nullable=True))
    
    # Safe updates with explicit boolean syntax for Postgres
    op.execute("UPDATE products SET is_hit = FALSE WHERE is_hit IS NULL")
    op.execute("UPDATE products SET is_discount = FALSE WHERE is_discount IS NULL")

def downgrade() -> None:
    op.drop_column('categories', 'image_url')
    op.drop_column('products', 'image_url')
    op.drop_column('products', 'is_discount')
    op.drop_column('products', 'is_hit')
