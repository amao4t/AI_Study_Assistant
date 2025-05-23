"""Initial migration

Revision ID: 442014fc3e44
Revises: 
Create Date: 2025-03-10 21:10:43.119952

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '442014fc3e44'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('document',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('file_type', sa.String(length=10), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('file_path', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('last_accessed', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('document_chunk',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chunk_text', sa.Text(), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('embedding_stored', sa.Boolean(), nullable=True),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('question',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('question_type', sa.String(length=10), nullable=False),
    sa.Column('options', sa.Text(), nullable=True),
    sa.Column('answer', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('study_session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('session_type', sa.String(length=20), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('study_session')
    op.drop_table('question')
    op.drop_table('document_chunk')
    op.drop_table('document')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    # ### end Alembic commands ###
