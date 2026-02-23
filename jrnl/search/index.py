# Copyright © 2012-2023 jrnl contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

"""SQLite-based semantic index for storing and searching entry embeddings.

The index is a derived, disposable cache — it can always be rebuilt from the
journal source text. It is stored as a SQLite file co-located with the journal.

For encrypted journals, all sensitive data (embeddings, dates, body hashes) is
packed into a single encrypted BLOB per row. Only the entry_id (a one-way
SHA256 hash) remains in cleartext.
"""

import datetime
import logging
import sqlite3
from typing import TYPE_CHECKING

import numpy as np

from jrnl.search.entry_id import body_hash as compute_body_hash
from jrnl.search.entry_id import entry_id as compute_entry_id

if TYPE_CHECKING:
    from jrnl.journals import Journal
    from jrnl.search.crypto import IndexKeyCrypto

_SCHEMA_VERSION = "1"


class SemanticIndex:
    """SQLite-backed vector index for semantic search."""

    def __init__(
        self,
        db_path: str,
        model_name: str,
        dimensions: int,
        crypto: "IndexKeyCrypto | None" = None,
    ):
        """Open or create the SQLite index.

        Args:
            db_path: Path to the SQLite database file (or ":memory:" for tests).
            model_name: Name of the embedding model (stored in meta).
            dimensions: Embedding vector dimensions.
            crypto: If provided, encrypt/decrypt payloads for encrypted journals.
        """
        self.db_path = db_path
        self.model_name = model_name
        self.dimensions = dimensions
        self._crypto = crypto
        self._encrypted = crypto is not None

        self.conn = sqlite3.connect(db_path)
        self._init_schema()
        self._check_meta()

    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS meta ("
            "    key   TEXT PRIMARY KEY,"
            "    value TEXT"
            ")"
        )

        if self._encrypted:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS embeddings ("
                "    entry_id  TEXT PRIMARY KEY,"
                "    payload   BLOB"
                ")"
            )
        else:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS embeddings ("
                "    entry_id    TEXT PRIMARY KEY,"
                "    entry_date  TEXT,"
                "    body_hash   TEXT,"
                "    embedding   BLOB,"
                "    indexed_at  TEXT"
                ")"
            )

        self.conn.commit()

    def _check_meta(self) -> None:
        """Verify or initialize meta table values.

        If the model has changed, clear the index so it gets rebuilt.
        """
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT value FROM meta WHERE key = 'model_name'"
        ).fetchone()

        if row is None:
            # First time — initialize
            cursor.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                ("model_name", self.model_name),
            )
            cursor.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                ("dimensions", str(self.dimensions)),
            )
            cursor.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                ("version", _SCHEMA_VERSION),
            )
            cursor.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                ("encrypted", str(self._encrypted)),
            )
            self.conn.commit()
        elif row[0] != self.model_name:
            logging.info(
                "Embedding model changed from %s to %s. Clearing index.",
                row[0],
                self.model_name,
            )
            self.clear()
            # Re-initialize meta with new model
            cursor.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                ("model_name", self.model_name),
            )
            cursor.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                ("dimensions", str(self.dimensions)),
            )
            self.conn.commit()

    def sync(self, journal: "Journal") -> dict:
        """Diff journal entries vs indexed entries.

        Returns:
            dict with keys "add", "update", "delete":
            - add: list of entries to embed and insert
            - update: list of entries to re-embed and update
            - delete: list of entry_id strings to remove
        """
        # Build current state from journal
        journal_entries = {}
        for entry in journal.entries:
            eid = compute_entry_id(entry)
            bhash = compute_body_hash(entry)
            journal_entries[eid] = {"entry": entry, "body_hash": bhash}

        # Build indexed state from database
        indexed = {}
        cursor = self.conn.cursor()

        if self._encrypted:
            from jrnl.search.crypto import unpack_payload

            rows = cursor.execute(
                "SELECT entry_id, payload FROM embeddings"
            ).fetchall()
            for eid, payload_blob in rows:
                try:
                    decrypted = self._crypto.decrypt_payload(payload_blob)
                    unpacked = unpack_payload(decrypted, self.dimensions)
                    indexed[eid] = unpacked["body_hash"]
                except Exception:
                    # If we can't decrypt, treat as needing re-index
                    indexed[eid] = None
        else:
            rows = cursor.execute(
                "SELECT entry_id, body_hash FROM embeddings"
            ).fetchall()
            for eid, bhash in rows:
                indexed[eid] = bhash

        # Compute diffs
        to_add = []
        to_update = []
        to_delete = []

        for eid, info in journal_entries.items():
            if eid not in indexed:
                to_add.append(info["entry"])
            elif indexed[eid] != info["body_hash"]:
                to_update.append(info["entry"])

        for eid in indexed:
            if eid not in journal_entries:
                to_delete.append(eid)

        return {"add": to_add, "update": to_update, "delete": to_delete}

    def store(
        self,
        eid: str,
        embedding: np.ndarray,
        entry_date: str,
        bhash: str,
    ) -> None:
        """Upsert one embedding. Encrypts payload if crypto is set."""
        now = datetime.datetime.now().isoformat()
        cursor = self.conn.cursor()

        if self._encrypted:
            from jrnl.search.crypto import pack_payload

            packed = pack_payload(embedding, entry_date, bhash, now)
            encrypted = self._crypto.encrypt_payload(packed)
            cursor.execute(
                "INSERT OR REPLACE INTO embeddings (entry_id, payload) VALUES (?, ?)",
                (eid, encrypted),
            )
        else:
            emb_blob = embedding.astype(np.float32).tobytes()
            cursor.execute(
                "INSERT OR REPLACE INTO embeddings "
                "(entry_id, entry_date, body_hash, embedding, indexed_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (eid, entry_date, bhash, emb_blob, now),
            )

        self.conn.commit()

    def store_batch(
        self,
        entries_data: list[tuple[str, np.ndarray, str, str]],
    ) -> None:
        """Store multiple embeddings in a single transaction.

        Args:
            entries_data: List of (entry_id, embedding, entry_date, body_hash) tuples.
        """
        now = datetime.datetime.now().isoformat()
        cursor = self.conn.cursor()

        if self._encrypted:
            from jrnl.search.crypto import pack_payload

            for eid, embedding, entry_date, bhash in entries_data:
                packed = pack_payload(embedding, entry_date, bhash, now)
                encrypted = self._crypto.encrypt_payload(packed)
                cursor.execute(
                    "INSERT OR REPLACE INTO embeddings (entry_id, payload) "
                    "VALUES (?, ?)",
                    (eid, encrypted),
                )
        else:
            for eid, embedding, entry_date, bhash in entries_data:
                emb_blob = embedding.astype(np.float32).tobytes()
                cursor.execute(
                    "INSERT OR REPLACE INTO embeddings "
                    "(entry_id, entry_date, body_hash, embedding, indexed_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (eid, entry_date, bhash, emb_blob, now),
                )

        self.conn.commit()

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        threshold: float = 0.4,
    ) -> list[tuple[str, float]]:
        """Brute-force cosine similarity search.

        Returns:
            List of (entry_id, score) tuples sorted by descending similarity.
        """
        cursor = self.conn.cursor()

        if self._encrypted:
            from jrnl.search.crypto import unpack_payload

            rows = cursor.execute(
                "SELECT entry_id, payload FROM embeddings"
            ).fetchall()
        else:
            rows = cursor.execute(
                "SELECT entry_id, embedding FROM embeddings"
            ).fetchall()

        if not rows:
            return []

        query_norm = query_embedding / np.linalg.norm(query_embedding)
        results = []

        for eid, blob in rows:
            if self._encrypted:
                try:
                    decrypted = self._crypto.decrypt_payload(blob)
                    unpacked = unpack_payload(decrypted, self.dimensions)
                    emb = unpacked["embedding"]
                except Exception:
                    logging.warning("Failed to decrypt embedding for %s, skipping", eid)
                    continue
            else:
                emb = np.frombuffer(blob, dtype=np.float32)

            emb_norm = np.linalg.norm(emb)
            if emb_norm == 0:
                continue
            score = float(np.dot(query_norm, emb / emb_norm))
            if score >= threshold:
                results.append((eid, score))

        return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]

    def delete(self, entry_ids: list[str]) -> None:
        """Remove entries from the index."""
        if not entry_ids:
            return
        cursor = self.conn.cursor()
        placeholders = ",".join("?" for _ in entry_ids)
        cursor.execute(
            f"DELETE FROM embeddings WHERE entry_id IN ({placeholders})",
            entry_ids,
        )
        self.conn.commit()

    def clear(self) -> None:
        """Drop all embeddings (for full reindex or model change)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM embeddings")
        self.conn.commit()

    def count(self) -> int:
        """Return the number of indexed entries."""
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT COUNT(*) FROM embeddings").fetchone()
        return row[0] if row else 0

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
