# Copyright © 2012-2023 jrnl contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

"""Embedding model loading and text encoding for semantic search.

Uses fastembed (ONNX backend) for lightweight CPU-friendly inference.
No PyTorch dependency required — install size ~100MB vs ~2GB.
"""

import logging
from typing import TYPE_CHECKING

import numpy as np

from jrnl.exception import JrnlException
from jrnl.messages import Message
from jrnl.messages import MsgStyle
from jrnl.messages import MsgText

if TYPE_CHECKING:
    from jrnl.journals import Entry

# Default model — BAAI/bge-small-en-v1.5
# 384 dimensions, ~50MB, 512 token context, strong MTEB retrieval scores
DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_DIMENSIONS = 384

# Maximum text length to send to the model (characters)
MAX_TEXT_LENGTH = 2048


def load_model(model_name: str = DEFAULT_MODEL):
    """Load embedding model via fastembed (ONNX backend).

    Args:
        model_name: HuggingFace model name.

    Returns:
        A fastembed TextEmbedding model instance.

    Raises:
        JrnlException: If fastembed is not installed.
    """
    try:
        from fastembed import TextEmbedding  # type: ignore[import-not-found]
    except ImportError:
        raise JrnlException(
            Message(MsgText.SemanticSearchNotInstalled, MsgStyle.ERROR)
        )

    logging.info("Loading embedding model: %s", model_name)
    return TextEmbedding(model_name)


def encode(model, texts: list[str]) -> list[np.ndarray]:
    """Generate embeddings for a list of texts.

    Args:
        model: A fastembed TextEmbedding instance.
        texts: List of text strings to encode.

    Returns:
        List of numpy arrays (one per text).
    """
    return list(model.embed(texts))


def encode_single(model, text: str) -> np.ndarray:
    """Generate embedding for a single text string.

    Args:
        model: A fastembed TextEmbedding instance.
        text: Text string to encode.

    Returns:
        Numpy array of the embedding.
    """
    results = list(model.embed([text]))
    return results[0]


def get_embeddable_text(entry: "Entry") -> str:
    """Prepare entry text for embedding.

    Combines title and body. Truncates to MAX_TEXT_LENGTH to avoid
    exceeding the model's token context window.
    """
    text = f"{entry.title}\n{entry.body}"
    return text[:MAX_TEXT_LENGTH]


def get_model_dimensions(model_name: str = DEFAULT_MODEL) -> int:
    """Return the embedding dimensions for a known model.

    Falls back to DEFAULT_DIMENSIONS for unknown models.
    """
    known_models = {
        "BAAI/bge-small-en-v1.5": 384,
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "BAAI/bge-base-en-v1.5": 768,
    }
    return known_models.get(model_name, DEFAULT_DIMENSIONS)
