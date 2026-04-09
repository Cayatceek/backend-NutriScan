"""Add user settings

Revision ID: 20260409_05
Revises: 20260409_04
Create Date: 2026-04-09 18:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260409_05"
down_revision = "20260409_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="uz"),
        sa.Column("is_language_manually_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("theme", sa.String(length=32), nullable=False, server_default="system"),
        sa.Column("halal_mode_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("healthy_mode_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("vegan_mode_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("selected_allergens", sa.JSON(), nullable=False),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("onboarding_shown", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_settings_id"), "user_settings", ["id"], unique=False)
    op.create_index(op.f("ix_user_settings_user_id"), "user_settings", ["user_id"], unique=False)

    bind = op.get_bind()
    users_table = sa.table("users", sa.column("id", sa.Integer()))
    settings_table = sa.table(
        "user_settings",
        sa.column("user_id", sa.Integer()),
        sa.column("language", sa.String()),
        sa.column("is_language_manually_selected", sa.Boolean()),
        sa.column("theme", sa.String()),
        sa.column("halal_mode_enabled", sa.Boolean()),
        sa.column("healthy_mode_enabled", sa.Boolean()),
        sa.column("vegan_mode_enabled", sa.Boolean()),
        sa.column("notifications_enabled", sa.Boolean()),
        sa.column("selected_allergens", sa.JSON()),
        sa.column("onboarding_completed", sa.Boolean()),
        sa.column("onboarding_shown", sa.Boolean()),
    )
    user_ids = [row.id for row in bind.execute(sa.select(users_table.c.id))]
    if user_ids:
        op.bulk_insert(
            settings_table,
            [
                {
                    "user_id": user_id,
                    "language": "uz",
                    "is_language_manually_selected": False,
                    "theme": "system",
                    "halal_mode_enabled": False,
                    "healthy_mode_enabled": False,
                    "vegan_mode_enabled": False,
                    "notifications_enabled": True,
                    "selected_allergens": [],
                    "onboarding_completed": False,
                    "onboarding_shown": False,
                }
                for user_id in user_ids
            ],
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_settings_user_id"), table_name="user_settings")
    op.drop_index(op.f("ix_user_settings_id"), table_name="user_settings")
    op.drop_table("user_settings")
