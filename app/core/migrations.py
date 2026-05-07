"""Apply Alembic revisions (synchronous; invoke via ``asyncio.to_thread`` at startup)."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def run_alembic_upgrade() -> None:
    project_root = Path(__file__).resolve().parents[2]
    ini_path = project_root / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(project_root / "alembic"))
    command.upgrade(cfg, "head")
