"""Crear roles predeterminados

Revision ID: 3f0abfa46c17
Revises: 7768698c0bfc
Create Date: 2026-08-27 13:27:44.117954

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f0abfa46c17'
down_revision = '7768698c0bfc'
branch_labels = None
depends_on = None


def upgrade():
    role_table = sa.table(
        'role',
        sa.column('nombre', sa.String(length=50)),
    )
    op.bulk_insert(role_table, [
        {'nombre': 'admin'},
        {'nombre': 'user'},
    ])


def downgrade():
    role_table = sa.table(
        'role',
        sa.column('nombre', sa.String(length=50)),
    )
    op.execute(role_table.delete().where(role_table.c.nombre.in_(['admin', 'user'])))
