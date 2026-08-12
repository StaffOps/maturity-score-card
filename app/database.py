import os
import json
import logging
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import ThreadedConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/maturity")
logger = logging.getLogger(__name__)

_pool: ThreadedConnectionPool | None = None


def init_db() -> None:
    global _pool
    _pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS metric_scores (
                    area         TEXT NOT NULL,
                    team         TEXT NOT NULL,
                    app          TEXT NOT NULL,
                    env          TEXT NOT NULL,
                    scorecard    TEXT NOT NULL,
                    metric       TEXT NOT NULL,
                    score        FLOAT NOT NULL,
                    weight       FLOAT NOT NULL,
                    raw          JSONB NOT NULL DEFAULT '{}',
                    project_repo TEXT,
                    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
                    PRIMARY KEY (area, team, app, env, scorecard, metric)
                )
            """)
            cur.execute("""
                ALTER TABLE metric_scores
                ADD COLUMN IF NOT EXISTS project_repo TEXT
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS problems (
                    area         TEXT NOT NULL,
                    team         TEXT NOT NULL,
                    app          TEXT NOT NULL,
                    env          TEXT NOT NULL,
                    problem_type TEXT NOT NULL,
                    severity     TEXT NOT NULL,
                    count        INTEGER NOT NULL DEFAULT 0,
                    details      JSONB NOT NULL DEFAULT '[]',
                    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
                    PRIMARY KEY (area, team, app, env, problem_type, severity)
                )
            """)
        conn.commit()


@contextmanager
def get_conn():
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        _pool.putconn(conn)


def upsert_score(area: str, team: str, app: str, env: str,
                 scorecard: str, metric: str, score: float, weight: float, raw: dict,
                 project_repo: str | None = None) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO metric_scores (area, team, app, env, scorecard, metric, score, weight, raw, project_repo, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (area, team, app, env, scorecard, metric)
                DO UPDATE SET score=EXCLUDED.score, weight=EXCLUDED.weight,
                              raw=EXCLUDED.raw, project_repo=EXCLUDED.project_repo, updated_at=now()
            """, (area, team, app, env, scorecard, metric, score, weight, json.dumps(raw), project_repo))
        conn.commit()


def upsert_problem(area: str, team: str, app: str, env: str,
                   problem_type: str, severity: str, count: int, details: list) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO problems (area, team, app, env, problem_type, severity, count, details, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (area, team, app, env, problem_type, severity)
                DO UPDATE SET count=EXCLUDED.count, details=EXCLUDED.details, updated_at=now()
            """, (area, team, app, env, problem_type, severity, count, json.dumps(details)))
        conn.commit()


def get_all_scores() -> list[tuple]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT area, team, app, env, scorecard, metric, score, weight, raw, project_repo
                FROM metric_scores
            """)
            return cur.fetchall()


def get_project_repos() -> list[tuple]:
    """One row per app: (area, team, app, env, project_repo).

    project_repo is stored per metric, so an app can end up with divergent values
    when only some pipeline steps send it. Collapsing to a single row here keeps
    maturity_project_info at exactly one series per app, which is what the
    group_left joins in the recording rules require.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (area, team, app, env)
                       area, team, app, env, COALESCE(project_repo, '')
                FROM metric_scores
                ORDER BY area, team, app, env,
                         (project_repo IS NOT NULL AND project_repo <> '') DESC,
                         updated_at DESC
            """)
            return cur.fetchall()


def get_all_problems() -> list[tuple]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT area, team, app, env, problem_type, severity, count
                FROM problems
            """)
            return cur.fetchall()
