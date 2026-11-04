"""Poolklassement: players en matches tabellen.

Revision ID: 9f3c1a2b7d84
Revises:
Create Date: 2026-11-02

"""

import sqlalchemy as sa
from alembic import op

revision: str = "9f3c1a2b7d84"
down_revision: str | None = None
branch_labels: tuple[str, ...] = ("poolklassement",)
depends_on: None = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("rating", sa.Float(), nullable=False, server_default="1200"),
        sa.Column("wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("losses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("draws", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_players_name", "players", ["name"], unique=True)
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("player_a_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("player_b_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("result", sa.String(length=4), nullable=False),
        sa.Column("rating_a_before", sa.Float(), nullable=False),
        sa.Column("rating_b_before", sa.Float(), nullable=False),
        sa.Column("rating_a_after", sa.Float(), nullable=False),
        sa.Column("rating_b_after", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("matches")
    op.drop_index("ix_players_name", table_name="players")
    op.drop_table("players")
