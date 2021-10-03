"""Migration to v0.4

Revision ID: 375fa26249aa
Revises: e3b75ad6d1c9
Create Date: 2021-10-02 17:34:15.813714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '375fa26249aa'
down_revision = 'e3b75ad6d1c9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('room',
    sa.Column('num', sa.Integer(), nullable=False),
    sa.Column('floor', sa.Integer(), nullable=True),
    sa.Column('base_ip', sa.String(length=4), nullable=True),
    sa.PrimaryKeyConstraint('num')
    )
    op.create_table('rental',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('_user_id', sa.Integer(), nullable=False),
    sa.Column('_room_num', sa.Integer(), nullable=False),
    sa.Column('start', sa.Date(), nullable=False),
    sa.Column('end', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['_room_num'], ['room.num'], ),
    sa.ForeignKeyConstraint(['_user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('rental')
    op.drop_table('room')
    # ### end Alembic commands ###
