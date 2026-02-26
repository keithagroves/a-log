# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

"""Public API for semantic search.

Provides three main functions:
- semantic_search(): Search journal entries by meaning
- build_index(): Build or rebuild the full semantic index
- update_index(): Incrementally update the index
"""

import logging
from typing import TYPE_CHECKING

from alog.exception import AlogException
from alog.messages import Message
from alog.messages import MsgStyle
from alog.messages import MsgText
from alog.output import print_msg
from alog.path import get_semantic_index_path
from alog.search.embeddings import DEFAULT_MODEL
from alog.search.embeddings import encode
from alog.search.embeddings import encode_single
from alog.search.embeddings import get_embeddable_text
from alog.search.embeddings import get_model_dimensions
from alog.search.embeddings import load_model
from alog.search.entry_id import body_hash as compute_body_hash
from alog.search.entry_id import entry_id as compute_entry_id
from alog.search.index import SemanticIndex

if TYPE_CHECKING:
    from alog.journals import Entry
    from alog.journals import Journal


def _get_journal_password(journal: "Journal") -> str | None:
    """Attempt to retrieve the current journal password from encryption method."""
    if getattr(journal, "encryption_method", None) is None:
        return None

    return getattr(journal.encryption_method, "password", None)


def _get_crypto(journal: "Journal", config: dict):
    """Get an IndexKeyCrypto instance if the journal is encrypted."""
    if not config.get("encrypt"):
        return None

    password = _get_journal_password(journal)
    if not password:
        raise AlogException(Message(MsgText.SemanticIndexEncrypted, MsgStyle.ERROR))

    from alog.search.crypto import IndexKeyCrypto

    return IndexKeyCrypto(password)


def _get_index(journal: "Journal", config: dict) -> SemanticIndex:
    """Create or open the SemanticIndex for the configured journal."""
    semantic_config = config.get("semantic_search", {})
    model_name = semantic_config.get("model", DEFAULT_MODEL)
    dimensions = get_model_dimensions(model_name)
    db_path = get_semantic_index_path(config["journal"])
    crypto = _get_crypto(journal, config)

    return SemanticIndex(
        db_path=db_path,
        model_name=model_name,
        dimensions=dimensions,
        crypto=crypto,
    )


def semantic_search(
    journal: "Journal",
    query: str,
    config: dict,
) -> list["Entry"]:
    """Search journal entries by meaning.

    1. Load model
    2. Open/sync index (auto-index if needed)
    3. Encode query
    4. Search index
    5. Map results back to Entry objects
    6. Return entries sorted by semantic similarity

    Args:
        journal: Journal instance (already opened with entries loaded).
        query: Natural language search query.
        config: Scoped config dict for this journal.

    Returns:
        List of Entry objects sorted by similarity (most similar first).
    """
    semantic_config = config.get("semantic_search", {})
    model_name = semantic_config.get("model", DEFAULT_MODEL)
    top_k = semantic_config.get("top_k", 10)
    threshold = semantic_config.get("threshold", 0.4)

    # Load model and index
    model = load_model(model_name)
    index = _get_index(journal, config)

    try:
        # Auto-sync: ensure index is up to date
        _sync_index(journal, index, model)

        # Encode query
        query_embedding = encode_single(model, query)

        # Search
        results = index.search(query_embedding, top_k=top_k, threshold=threshold)

        if not results:
            print_msg(Message(MsgText.SemanticNoResults, MsgStyle.NORMAL))
            return []

        # Map entry_ids back to Entry objects
        entry_id_map = {}
        for entry in journal.entries:
            eid = compute_entry_id(entry)
            entry_id_map[eid] = entry

        matched_entries = []
        for eid, score in results:
            if eid in entry_id_map:
                entry = entry_id_map[eid]
                logging.debug("Semantic match: %.3f - %s", score, entry.title[:50])
                matched_entries.append(entry)

        return matched_entries
    finally:
        index.close()


def build_index(journal: "Journal", config: dict) -> None:
    """Build or rebuild the full semantic index for a journal.

    Clears any existing index and re-embeds all entries.

    Args:
        journal: Journal instance (already opened with entries loaded).
        config: Scoped config dict for this journal.
    """
    semantic_config = config.get("semantic_search", {})
    model_name = semantic_config.get("model", DEFAULT_MODEL)

    model = load_model(model_name)
    index = _get_index(journal, config)

    try:
        index.clear()

        entries = journal.entries
        if not entries:
            logging.info("No entries to index.")
            return

        # Prepare texts
        texts = [get_embeddable_text(entry) for entry in entries]
        logging.info("Indexing %d entries...", len(texts))

        # Batch encode
        embeddings = encode(model, texts)

        # Store all
        batch_data = []
        for entry, embedding in zip(entries, embeddings):
            eid = compute_entry_id(entry)
            bhash = compute_body_hash(entry)
            date_str = entry.date.isoformat()
            batch_data.append((eid, embedding, date_str, bhash))

        index.store_batch(batch_data)
        logging.info("Indexed %d entries.", len(batch_data))
    finally:
        index.close()


def update_index(journal: "Journal", config: dict) -> None:
    """Incrementally update the index.

    Only embeds new or changed entries. Removes deleted entries.

    Args:
        journal: Journal instance (already opened with entries loaded).
        config: Scoped config dict for this journal.
    """
    semantic_config = config.get("semantic_search", {})
    model_name = semantic_config.get("model", DEFAULT_MODEL)

    model = load_model(model_name)
    index = _get_index(journal, config)

    try:
        _sync_index(journal, index, model)
    finally:
        index.close()


def _sync_index(journal: "Journal", index: SemanticIndex, model) -> None:
    """Internal: sync the index with current journal state."""
    diff = index.sync(journal)

    to_add = diff["add"]
    to_update = diff["update"]
    to_delete = diff["delete"]

    if not to_add and not to_update and not to_delete:
        logging.debug("Semantic index is up to date.")
        return

    logging.info(
        "Semantic index sync: %d to add, %d to update, %d to delete",
        len(to_add),
        len(to_update),
        len(to_delete),
    )

    # Delete removed entries
    if to_delete:
        index.delete(to_delete)

    # Embed and store new + updated entries
    all_entries = to_add + to_update
    if all_entries:
        texts = [get_embeddable_text(entry) for entry in all_entries]
        embeddings = encode(model, texts)

        batch_data = []
        for entry, embedding in zip(all_entries, embeddings):
            eid = compute_entry_id(entry)
            bhash = compute_body_hash(entry)
            date_str = entry.date.isoformat()
            batch_data.append((eid, embedding, date_str, bhash))

        index.store_batch(batch_data)
