import os
import shutil
import tempfile
import uuid
from pathlib import Path


class LocalStorageService:
    """Local filesystem storage abstraction for upload workflows."""

    def __init__(self, base_dir: Path | None = None, tmp_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parents[2] / "media"
        self.tmp_dir = tmp_dir or Path(tempfile.gettempdir())

    def save_temp(self, data: bytes, filename: str) -> Path:
        suffix = Path(filename).suffix or ".upload"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.tmp_dir / f"{uuid.uuid4()}{suffix}.upload"
        tmp_path.write_bytes(data)
        return tmp_path

    def finalize(self, tmp_path: Path, dest_path: Path) -> Path:
        absolute_dest = self.base_dir / dest_path
        absolute_dest.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp_path, absolute_dest)
        return absolute_dest

    def delete_if_exists(self, path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            if path.exists():
                raise

    def exists(self, dest_path: Path) -> bool:
        return (self.base_dir / dest_path).exists()

    def clear_media(self) -> None:
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
