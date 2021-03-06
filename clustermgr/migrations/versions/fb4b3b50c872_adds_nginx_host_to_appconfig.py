"""adds nginx_host to appconfig

Revision ID: fb4b3b50c872
Revises: 5246a3f7a7e4
Create Date: 2017-09-30 14:54:52.736109

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb4b3b50c872'
down_revision = '5246a3f7a7e4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('appconfig', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nginx_host', sa.String(length=250), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('appconfig', schema=None) as batch_op:
        batch_op.drop_column('nginx_host')

    # ### end Alembic commands ###
