"""Add optimization fields to EmailTask

Revision ID: optimize_email_task
Revises: 
Create Date: 2025-10-29 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'optimize_email_task'
down_revision = None  # Actualizar con tu última revisión
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columna error_message
    op.add_column('email_tasks', sa.Column('error_message', sa.Text(), nullable=True))
    
    # Agregar columna last_attempt_at
    op.add_column('email_tasks', sa.Column('last_attempt_at', sa.TIMESTAMP(), nullable=True))
    
    # Hacer uid UNIQUE (si no lo es ya)
    try:
        op.alter_column('email_tasks', 'uid',
                       existing_type=sa.String(255),
                       nullable=False)
        op.create_unique_constraint('uq_email_tasks_uid', 'email_tasks', ['uid'])
    except:
        print("UID constraint already exists or uid is already NOT NULL")
    
    # Agregar índice en status (si no existe ya)
    try:
        op.create_index('ix_email_tasks_status', 'email_tasks', ['status'])
    except:
        print("Status index already exists")
    
    # Agregar nuevos estados posibles a través de CHECK constraint (opcional en PostgreSQL)
    # Los estados ahora incluyen: 'pending', 'processing', 'done', 'failed', 'dead_letter', 'reprocessing'


def downgrade():
    # Eliminar índice de status
    try:
        op.drop_index('ix_email_tasks_status', table_name='email_tasks')
    except:
        pass
    
    # Eliminar unique constraint de uid
    try:
        op.drop_constraint('uq_email_tasks_uid', 'email_tasks', type_='unique')
    except:
        pass
    
    # Eliminar columnas nuevas
    op.drop_column('email_tasks', 'last_attempt_at')
    op.drop_column('email_tasks', 'error_message')
