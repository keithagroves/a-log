# Copyright © 2012-2023 jrnl contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jrnl.journals import Entry


def entry_id(entry: "Entry") -> str:
    """Stable hash from date + title.

    Uses date + title (not body) so that:
    - Body edits keep the same ID (detect "needs re-embedding")
    - Title changes create a new ID (semantically different entry)
    """
    raw = f"{entry.date.isoformat()}|{entry.title}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def body_hash(entry: "Entry") -> str:
    """Hash of body text to detect content changes."""
    return hashlib.sha256(entry.body.encode()).hexdigest()[:16]
