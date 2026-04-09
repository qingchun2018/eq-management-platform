"""
以 UTF-8 读取 seed.sql 并通过 psql 标准输入执行。

说明：Windows 下使用「psql -f seed.sql」时，客户端可能按系统编码（如 GBK）读文件，
会导致 UTF-8 中文与数据库 UTF8 编码冲突。本脚本用 Python 按 UTF-8 读入再交给 psql。

用法（在 backend 目录、已激活 .venv）:
  python scripts/import_seed_utf8.py
  python scripts/import_seed_utf8.py --reset   # 先清空 tags/tickets/ticket_tags 再导入

密码从 backend/.env 的 DATABASE_URL 解析，无需交互输入。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

BACKEND_DIR = Path(__file__).resolve().parent.parent
SEED_FILE = BACKEND_DIR / "seed.sql"


def find_psql() -> str:
    """在常见安装路径下查找 psql.exe。"""
    for ver in range(18, 12, -1):
        candidate = Path(rf"C:\Program Files\PostgreSQL\{ver}\bin\psql.exe")
        if candidate.is_file():
            return str(candidate)
    return "psql"


def _psql_args(psql: str, host: str, port: str, user: str, dbname: str) -> list[str]:
    return [
        psql,
        "-h",
        host,
        "-p",
        port,
        "-U",
        user,
        "-d",
        dbname,
        "-v",
        "ON_ERROR_STOP=1",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="以 UTF-8 导入 seed.sql")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="导入前先清空 ticket_tags、tickets、tags（避免重复键）",
    )
    args = parser.parse_args()

    if not SEED_FILE.is_file():
        print(f"未找到: {SEED_FILE}", file=sys.stderr)
        return 1

    # 确保能加载 app.config（依赖 .env）
    sys.path.insert(0, str(BACKEND_DIR))
    os.chdir(BACKEND_DIR)
    from app.config import settings

    sql = SEED_FILE.read_text(encoding="utf-8")
    psql = find_psql()

    raw = settings.sqlalchemy_database_url
    if raw.startswith("postgresql+psycopg://"):
        raw = "postgresql://" + raw[len("postgresql+psycopg://") :]
    u = urlparse(raw)

    env = os.environ.copy()
    env["PGCLIENTENCODING"] = "UTF8"
    if u.password:
        env["PGPASSWORD"] = unquote(u.password)

    host = u.hostname or "localhost"
    port = str(u.port or 5432)
    user = unquote(u.username) if u.username else "postgres"
    dbname = (u.path or "/").lstrip("/").split("/")[0] or "postgres"

    base_args = _psql_args(psql, host, port, user, dbname)

    if args.reset:
        truncate_sql = (
            "TRUNCATE TABLE ticket_tags, tickets, tags RESTART IDENTITY CASCADE;"
        )
        tr = subprocess.run(
            [
                psql,
                "-h",
                host,
                "-p",
                port,
                "-U",
                user,
                "-d",
                dbname,
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                truncate_sql,
            ],
            cwd=str(BACKEND_DIR),
            env=env,
        )
        if tr.returncode != 0:
            return tr.returncode

    proc = subprocess.run(
        base_args,
        input=sql.encode("utf-8"),
        cwd=str(BACKEND_DIR),
        env=env,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
