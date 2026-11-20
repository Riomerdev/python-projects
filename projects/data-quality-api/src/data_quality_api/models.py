from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class ImportRun(Base):
    __tablename__ = "import_runs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    rows_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    issues: Mapped[list["ImportIssue"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class AcceptedOrder(Base):
    __tablename__ = "accepted_orders"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_accepted_orders_external_id"),
        CheckConstraint("quantity > 0", name="ck_accepted_orders_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_accepted_orders_unit_price_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    import_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("import_runs.id", ondelete="RESTRICT"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(80), nullable=False)
    sku: Mapped[str] = mapped_column(String(40), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class ImportIssue(Base):
    __tablename__ = "import_issues"
    __table_args__ = (Index("ix_import_issues_import_row", "import_id", "row_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(80))
    messages: Mapped[str] = mapped_column(Text, nullable=False)
    run: Mapped[ImportRun] = relationship(back_populates="issues")
