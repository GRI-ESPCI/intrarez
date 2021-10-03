"""Migration to v0.3

Revision ID: e3b75ad6d1c9
Revises: d74742170f04
Create Date: 2021-09-26 19:39:25.362747

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3b75ad6d1c9'
down_revision = 'd74742170f04'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('nom', sa.String(length=64), nullable=True))
    op.add_column('user', sa.Column('prenom', sa.String(length=64), nullable=True))
    op.add_column('user', sa.Column('promo', sa.String(length=8), nullable=True))
    op.add_column('user', sa.Column('is_gri', sa.Boolean(), nullable=True))
    op.execute("UPDATE user SET is_gri = false")
    op.alter_column('user', 'is_gri', type_=sa.Boolean(), nullable=False)

    op.create_table('device',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('_user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('mac_address', sa.String(length=17), nullable=False),
    sa.Column('type', sa.String(length=64), nullable=True),
    sa.Column('registered', sa.DateTime(), nullable=False),
    sa.Column('last_seen', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('mac_address'),
    sa.ForeignKeyConstraint(['_user_id'], ['user.id'])
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'is_gri')
    op.drop_column('user', 'promo')
    op.drop_column('user', 'prenom')
    op.drop_column('user', 'nom')
    op.drop_table('device')
    # ### end Alembic commands ###