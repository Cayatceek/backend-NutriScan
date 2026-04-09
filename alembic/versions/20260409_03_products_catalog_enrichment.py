"""Enrich products catalog schema

Revision ID: 20260409_03
Revises: 20260409_02
Create Date: 2026-04-09 18:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260409_03"
down_revision = "20260409_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("image_url", sa.String(length=1024), nullable=True))
    op.add_column("products", sa.Column("image_front_url", sa.String(length=1024), nullable=True))
    op.add_column("products", sa.Column("nutriscore_grade", sa.String(length=8), nullable=True))
    op.add_column("products", sa.Column("ingredients_text", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("ingredients_json", sa.JSON(), nullable=True))
    op.add_column("products", sa.Column("categories", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("labels", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("additives_tags_json", sa.JSON(), nullable=True))
    op.add_column("products", sa.Column("allergens", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("nutriments_json", sa.JSON(), nullable=True))
    op.add_column("products", sa.Column("source", sa.String(length=32), nullable=True, server_default="api"))
    op.add_column(
        "products",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.execute("UPDATE products SET source = 'api' WHERE source IS NULL")
    op.alter_column("products", "source", existing_type=sa.String(length=32), nullable=False)
    op.create_index(op.f("ix_products_nutriscore_grade"), "products", ["nutriscore_grade"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_products_nutriscore_grade"), table_name="products")
    op.drop_column("products", "updated_at")
    op.drop_column("products", "source")
    op.drop_column("products", "nutriments_json")
    op.drop_column("products", "allergens")
    op.drop_column("products", "additives_tags_json")
    op.drop_column("products", "labels")
    op.drop_column("products", "categories")
    op.drop_column("products", "ingredients_json")
    op.drop_column("products", "ingredients_text")
    op.drop_column("products", "nutriscore_grade")
    op.drop_column("products", "image_front_url")
    op.drop_column("products", "image_url")
