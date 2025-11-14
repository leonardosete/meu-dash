"""Add report bundle table

Revision ID: 8b4d203f5c2a
Revises: 1367ea047777
Create Date: 2025-11-14 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8b4d203f5c2a"
down_revision = "1367ea047777"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "report_bundle",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("run_folder", sa.String(length=255), nullable=False),
        sa.Column("bundle", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["report_id"], ["report.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id"),
        sa.UniqueConstraint("run_folder"),
    )


def downgrade():
    op.drop_table("report_bundle")
