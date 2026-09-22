import os
import subprocess
from pathlib import Path

from sqlalchemy import create_engine, inspect


def test_clean_alembic_upgrade_to_head(tmp_path):
    backend = Path(__file__).parents[1]
    database = tmp_path / "migration.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{database.as_posix()}"
    result = subprocess.run(
        [os.sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    tables = set(inspect(create_engine(env["DATABASE_URL"])).get_table_names())
    assert {"blog_posts", "campaigns", "social_posts", "oauth_tokens", "processed_webhooks"} <= tables
