"""add last_tls_notified

Revision ID: 8d84111ae648
Revises: 800b65046cc2
Create Date: 2023-02-10 10:05:39.168607

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d84111ae648'
down_revision = '800b65046cc2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('servers', sa.Column('last_tls_notified', sa.DateTime(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('servers', 'last_tls_notified')
    # ### end Alembic commands ###