"""Create import run, accepted order and quarantine tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261120_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("filename", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("rows_total", sa.Integer(), nullable=False),
        sa.Column("rows_accepted", sa.Integer(), nullable=False),
        sa.Column("rows_rejected", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "accepted_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(length=80), nullable=False),
        sa.Column("sku", sa.String(length=40), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["import_runs.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("external_id", name="uq_accepted_orders_external_id"),
        sa.CheckConstraint("quantity > 0", name="ck_accepted_orders_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_accepted_orders_unit_price_nonnegative"),
    )
    op.create_table(
        "import_issues",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True, nullable=False),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=80), nullable=True),
        sa.Column("messages", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["import_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_import_issues_import_row", "import_issues", ["import_id", "row_number"])


def downgrade() -> None:
    op.drop_index("ix_import_issues_import_row", table_name="import_issues")
    op.drop_table("import_issues")
    op.drop_table("accepted_orders")
    op.drop_table("import_runs")
