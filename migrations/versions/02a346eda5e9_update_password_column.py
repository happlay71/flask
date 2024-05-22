"""Update password column

Revision ID: 02a346eda5e9
Revises: e78091b264a7
Create Date: 2023-06-30 16:04:49.960923

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '02a346eda5e9'
down_revision = 'e78091b264a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=128), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('password_hash')

    # ### end Alembic commands ###
