"""File acquisition and content-addressed provenance helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from pt_he_pipeline.types import SourceReceipt


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest of a file.

    Args:
        path: Existing file path.
        chunk_size: Number of bytes read per iteration.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If ``chunk_size`` is not positive.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not path.is_file():
        raise FileNotFoundError(path)

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_with_receipt(
    url: str,
    output: Path,
    *,
    timeout_seconds: float = 60.0,
    overwrite: bool = False,
) -> SourceReceipt:
    """Download ``url`` and write a JSON provenance receipt.

    The source bytes are written atomically through a temporary file. Existing
    output is protected unless ``overwrite=True``.
    """

    if not url.startswith(("https://", "http://")):
        raise ValueError("url must use http or https")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if output.exists() and not overwrite:
        raise FileExistsError(output)

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")

    with requests.get(url, timeout=timeout_seconds, stream=True) as response:
        response.raise_for_status()
        with temporary.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)

    temporary.replace(output)
    receipt = SourceReceipt(
        url=url,
        retrieved_at_utc=datetime.now(UTC).isoformat(),
        size_bytes=output.stat().st_size,
        sha256=sha256_file(output),
        path=output,
    )
    write_receipt(receipt)
    return receipt


def write_receipt(receipt: SourceReceipt) -> Path:
    """Write a stable JSON receipt next to a source file."""

    receipt_path = receipt.path.with_suffix(receipt.path.suffix + ".receipt.json")
    payload: dict[str, Any] = {
        "url": receipt.url,
        "retrieved_at_utc": receipt.retrieved_at_utc,
        "size_bytes": receipt.size_bytes,
        "sha256": receipt.sha256,
        "path": str(receipt.path),
    }
    receipt_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt_path
