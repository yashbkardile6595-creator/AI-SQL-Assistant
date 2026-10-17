"""Core logic: schema discovery, SQL generation, validation, and read-only execution."""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from langchain_community.utilities import SQLDatabase
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

ROOT = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(ROOT / "data" / "sales.db")))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
SQL_PROMPT = PromptTemplate.from_template("""
You write SQLite SELECT queries for a business analytics assistant.
Use ONLY tables and columns listed in the schema.
Rules:
- Return exactly one SQL query and nothing else.
- The query must be read-only and start with SELECT or WITH.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, ATTACH, PRAGMA, or multiple statements.
- Use explicit joins when needed.
- For ranking questions, sort by the relevant aggregate and add LIMIT.
- Add LIMIT 100 unless the query is an aggregate returning fewer rows.
- If the question cannot be answered from the schema, return: -- CANNOT_ANSWER

Database schema:
{schema}

Question: {question}

SQL:
""".strip())

class SQLAssistant:
    def __init__(self, database_path: Path = DATABASE_PATH, model: str = OLLAMA_MODEL):
        self.database_path = Path(database_path)
        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Database not found at {self.database_path}. Run: python setup_database.py"
            )
        # SQLDatabase is used for safe schema introspection and LLM context.
        self.db = SQLDatabase.from_uri(f"sqlite:///{self.database_path.as_posix()}")
        self.llm = OllamaLLM(model=model, temperature=0)
        self.schema = self.db.get_table_info()

    def generate_sql(self, question: str) -> str:
        if not question or not question.strip():
            raise ValueError("Please enter a question.")
        prompt = SQL_PROMPT.format(schema=self.schema, question=question.strip())
        raw = self.llm.invoke(prompt)
        sql = self._clean_sql(str(raw))
        self.validate_sql(sql)
        return sql

    @staticmethod
    def _clean_sql(raw: str) -> str:
        value = raw.strip()
        value = re.sub(r"^```(?:sql)?\s*", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\s*```$", "", value)
        value = re.sub(r"^(SQLQuery|SQL)\s*:\s*", "", value, flags=re.IGNORECASE)
        # Keep only the first statement; validation also rejects trailing statements.
        return value.strip()

    @staticmethod
    def validate_sql(sql: str) -> None:
        normalized = sql.strip().lower()
        if normalized.startswith("-- cannot_answer"):
            raise ValueError("I couldn't map that question to the available database schema.")
        if not (normalized.startswith("select") or normalized.startswith("with")):
            raise ValueError("Blocked: only SELECT queries are allowed.")
        # Remove quoted strings before checking dangerous tokens and semicolons.
        scrubbed = re.sub(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"", "''", normalized)
        if ";" in scrubbed.rstrip(";"):
            raise ValueError("Blocked: multiple SQL statements are not allowed.")
        forbidden = r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|vacuum|reindex|load_extension)\b"
        if re.search(forbidden, scrubbed):
            raise ValueError("Blocked: query contains a prohibited SQL operation.")
        if "--" in scrubbed or "/*" in scrubbed or "*/" in scrubbed:
            raise ValueError("Blocked: SQL comments are not allowed.")

    def execute_sql(self, sql: str) -> list[dict[str, Any]]:
        self.validate_sql(sql)
        # Open database in read-only mode; query_only adds another SQLite safeguard.
        uri = f"file:{self.database_path.resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA query_only = ON")
            conn.set_progress_handler(lambda: 1, 100_000)  # abort excessively expensive queries
            cursor = conn.execute(sql)
            columns = [item[0] for item in (cursor.description or [])]
            rows = cursor.fetchmany(101)
            if len(rows) > 100:
                rows = rows[:100]
            return [{columns[i]: row[i] for i in range(len(columns))} for row in rows]
        finally:
            conn.close()

    def ask(self, question: str) -> tuple[str, list[dict[str, Any]]]:
        sql = self.generate_sql(question)
        return sql, self.execute_sql(sql)
