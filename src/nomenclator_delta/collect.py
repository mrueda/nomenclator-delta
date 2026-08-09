from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from nomenclator_delta.schema import PARSER_VERSION


SNAPSHOT_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def collect_snapshot(
    snapshot: str,
    source_root: Path,
    source_url: str,
    timeout: int = 120,
) -> dict[str, Any]:
    if not SNAPSHOT_RE.fullmatch(snapshot):
        raise ValueError(f"invalid snapshot identifier: {snapshot}")

    artifact_dir = source_root / "artifacts" / snapshot
    metadata_dir = source_root / "metadata" / snapshot
    artifact_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    with requests.get(source_url, timeout=timeout, stream=True) as response:
        response.raise_for_status()
        original_filename = response_filename(response.headers) or f"nomenclator-{snapshot}.csv"
        digest = hashlib.sha256()
        size = 0
        with tempfile.NamedTemporaryFile(dir=artifact_dir, delete=False) as handle:
            temporary_path = Path(handle.name)
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                digest.update(chunk)
                size += len(chunk)
                handle.write(chunk)
        mime_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip()

    sha256 = digest.hexdigest()
    suffix = Path(original_filename).suffix or mimetypes.guess_extension(mime_type) or ".bin"
    artifact_path = artifact_dir / f"{sha256}{suffix}"
    if artifact_path.exists():
        temporary_path.unlink()
    else:
        temporary_path.replace(artifact_path)

    metadata = {
        "authority": "Ministerio de Sanidad",
        "source_url": source_url,
        "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "snapshot": snapshot,
        "original_filename": original_filename,
        "mime_type": mime_type or "application/octet-stream",
        "sha256": sha256,
        "file_size": size,
        "parser_version": PARSER_VERSION,
        "artifact": str(artifact_path),
    }
    metadata_path = metadata_dir / f"{sha256}.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def response_filename(headers: requests.structures.CaseInsensitiveDict[str]) -> str | None:
    disposition = headers.get("Content-Disposition", "")
    match = re.search(r"filename\*?=(?:UTF-8''|\")?([^\";]+)", disposition, re.IGNORECASE)
    return Path(match.group(1).strip()).name if match else None
