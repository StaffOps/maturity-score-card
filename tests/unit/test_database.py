"""Database layer tests against a fake connection pool (no PostgreSQL needed).

They check the contract of each function: the parameters it sends, that writes
commit, and that the connection always goes back to the pool.
"""
import json
from unittest.mock import MagicMock

import pytest

from app import database


@pytest.fixture()
def pool(monkeypatch):
    """Replace the module pool with a mock; yields (pool, conn, cursor)."""
    cursor = MagicMock()
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    fake_pool = MagicMock()
    fake_pool.getconn.return_value = conn
    monkeypatch.setattr(database, "_pool", fake_pool)
    return fake_pool, conn, cursor


class TestGetConn:
    def test_returns_connection_to_pool(self, pool):
        fake_pool, conn, _ = pool
        with database.get_conn() as c:
            assert c is conn
        fake_pool.putconn.assert_called_once_with(conn)

    def test_returns_connection_to_pool_on_error(self, pool):
        fake_pool, conn, _ = pool
        with pytest.raises(RuntimeError):
            with database.get_conn():
                raise RuntimeError("query failed")
        fake_pool.putconn.assert_called_once_with(conn)


class TestInitDb:
    def test_creates_pool_and_schema(self, monkeypatch):
        cursor = MagicMock()
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor
        created = MagicMock()
        created.getconn.return_value = conn
        pool_cls = MagicMock(return_value=created)
        monkeypatch.setattr(database, "ThreadedConnectionPool", pool_cls)
        monkeypatch.setattr(database, "_pool", None)

        database.init_db()

        pool_cls.assert_called_once_with(minconn=1, maxconn=10, dsn=database.DATABASE_URL)
        assert database._pool is created
        statements = " ".join(call.args[0] for call in cursor.execute.call_args_list)
        assert "CREATE TABLE IF NOT EXISTS metric_scores" in statements
        assert "ADD COLUMN IF NOT EXISTS project_repo" in statements
        assert "CREATE TABLE IF NOT EXISTS problems" in statements
        conn.commit.assert_called_once()
        created.putconn.assert_called_once_with(conn)


class TestUpsertScore:
    def test_sends_parameters_and_commits(self, pool):
        _, conn, cursor = pool
        raw = {"percentage": 80}
        database.upsert_score("fin", "pay", "api", "prd", "application",
                              "unit_coverage", 100.0, 1.5, raw, "org/api")

        sql, params = cursor.execute.call_args.args
        assert "ON CONFLICT (area, team, app, env, scorecard, metric)" in sql
        assert params == ("fin", "pay", "api", "prd", "application",
                          "unit_coverage", 100.0, 1.5, json.dumps(raw), "org/api")
        conn.commit.assert_called_once()

    def test_project_repo_defaults_to_none(self, pool):
        _, _, cursor = pool
        database.upsert_score("fin", "pay", "api", "prd", "security",
                              "sast", 90.0, 1.0, {})
        _, params = cursor.execute.call_args.args
        assert params[-1] is None
        assert params[-2] == "{}"


class TestUpsertProblem:
    def test_serializes_details_and_commits(self, pool):
        _, conn, cursor = pool
        details = [{"file": "main.tf", "line": 3}]
        database.upsert_problem("fin", "pay", "infra", "dev",
                                "secret_in_terraform", "critical", 1, details)

        sql, params = cursor.execute.call_args.args
        assert "INSERT INTO problems" in sql
        assert params == ("fin", "pay", "infra", "dev", "secret_in_terraform",
                          "critical", 1, json.dumps(details))
        conn.commit.assert_called_once()


class TestReads:
    @pytest.mark.parametrize("func, table", [
        (database.get_all_scores, "metric_scores"),
        (database.get_project_repos, "metric_scores"),
        (database.get_all_problems, "problems"),
    ])
    def test_returns_fetched_rows_without_commit(self, pool, func, table):
        fake_pool, conn, cursor = pool
        rows = [("fin", "pay", "api", "prd")]
        cursor.fetchall.return_value = rows

        assert func() == rows
        assert f"FROM {table}" in cursor.execute.call_args.args[0]
        conn.commit.assert_not_called()
        fake_pool.putconn.assert_called_once_with(conn)

    def test_project_repos_collapses_to_one_row_per_app(self, pool):
        _, _, cursor = pool
        cursor.fetchall.return_value = []
        database.get_project_repos()
        sql = cursor.execute.call_args.args[0]
        # One series per app is what the group_left joins in the recording rules need.
        assert "DISTINCT ON (area, team, app, env)" in sql
        assert "COALESCE(project_repo, '')" in sql
