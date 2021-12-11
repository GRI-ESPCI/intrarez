"""Migration to v1.4

Revision ID: 586cce08f52a
Revises: 720dac88262b
Create Date: 2021-12-08 01:51:23.868076

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '586cce08f52a'
down_revision = '720dac88262b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    postgresql.ENUM('subscribed', 'trial', 'outlaw',
                    name='substate').create(op.get_bind())

    enum = sa.Enum('subscribed', 'trial', 'outlaw', name='substate')
    op.add_column('rezident', sa.Column('sub_state', enum, nullable=True))
    op.execute("UPDATE rezident SET sub_state = 'trial'")
    op.alter_column('rezident', 'sub_state', type_=enum, nullable=False)

    op.create_table('offer',
    sa.Column('slug', sa.String(length=32), nullable=False),
    sa.Column('name_fr', sa.String(length=64), nullable=False),
    sa.Column('name_en', sa.String(length=64), nullable=False),
    sa.Column('description_fr', sa.String(length=2000), nullable=True),
    sa.Column('description_en', sa.String(length=2000), nullable=True),
    sa.Column('price', sa.Numeric(precision=6, scale=2, asdecimal=False),
              nullable=True),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('slug')
    )
    op.create_table('payment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('_rezident_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=6, scale=2, asdecimal=False),
              nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('lydia', sa.Boolean(), nullable=False),
    sa.Column('lydia_id', sa.BigInteger(), nullable=True),
    sa.Column('_gri_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['_gri_id'], ['rezident.id'], ),
    sa.ForeignKeyConstraint(['_rezident_id'], ['rezident.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('subscription',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('_rezident_id', sa.Integer(), nullable=False),
    sa.Column('_offer_slug', sa.String(length=32), nullable=False),
    sa.Column('_payment_id', sa.Integer(), nullable=True),
    sa.Column('start', sa.Date(), nullable=False),
    sa.Column('end', sa.Date(), nullable=False),
    sa.ForeignKeyConstraint(['_offer_slug'], ['offer.slug'], ),
    sa.ForeignKeyConstraint(['_payment_id'], ['payment.id'], ),
    sa.ForeignKeyConstraint(['_rezident_id'], ['rezident.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('subscription')
    op.drop_table('payment')
    op.drop_table('offer')
    op.drop_column('rezident', 'sub_state')

    postgresql.ENUM('subscribed', 'trial', 'outlaw',
                    name='substate').drop(op.get_bind())
    # ### end Alembic commands ###
