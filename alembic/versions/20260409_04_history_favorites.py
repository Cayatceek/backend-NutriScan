"""Add history and favorites

Revision ID: 20260409_04
Revises: 20260409_03
Create Date: 2026-04-09 18:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260409_04"
down_revision = "20260409_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "favorite_products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_favorite_products_user_product"),
    )
    op.create_index(op.f("ix_favorite_products_id"), "favorite_products", ["id"], unique=False)
    op.create_index(op.f("ix_favorite_products_product_id"), "favorite_products", ["product_id"], unique=False)
    op.create_index(op.f("ix_favorite_products_user_id"), "favorite_products", ["user_id"], unique=False)

    op.create_table(
        "scan_history",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scan_history_product_id"), "scan_history", ["product_id"], unique=False)
    op.create_index(op.f("ix_scan_history_scanned_at"), "scan_history", ["scanned_at"], unique=False)
    op.create_index(op.f("ix_scan_history_user_id"), "scan_history", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_scan_history_user_id"), table_name="scan_history")
    op.drop_index(op.f("ix_scan_history_scanned_at"), table_name="scan_history")
    op.drop_index(op.f("ix_scan_history_product_id"), table_name="scan_history")
    op.drop_table("scan_history")

    op.drop_index(op.f("ix_favorite_products_user_id"), table_name="favorite_products")
    op.drop_index(op.f("ix_favorite_products_product_id"), table_name="favorite_products")
    op.drop_index(op.f("ix_favorite_products_id"), table_name="favorite_products")
    op.drop_table("favorite_products")
