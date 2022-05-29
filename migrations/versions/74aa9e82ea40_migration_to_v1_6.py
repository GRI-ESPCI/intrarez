"""Migration to v1.6

Revision ID: 74aa9e82ea40
Revises: 586cce08f52a
Create Date: 2022-02-12 03:26:41.125807

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "74aa9e82ea40"
down_revision = "586cce08f52a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "ban",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("_rezident_id", sa.Integer(), nullable=False),
        sa.Column("start", sa.DateTime(), nullable=False),
        sa.Column("end", sa.DateTime(), nullable=True),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("message", sa.String(length=2000), nullable=True),
        sa.ForeignKeyConstraint(
            ["_rezident_id"],
            ["rezident.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("ban")
    # ### end Alembic commands ###