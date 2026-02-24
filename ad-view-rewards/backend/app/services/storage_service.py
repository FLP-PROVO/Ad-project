import base64
import hashlib
import hmac
import json
import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from uuid import UUID

from app.core.config import settings


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

    def generate_signed_url(self, file_path: str, user_id: UUID, expires_seconds: int = 300) -> str:
        expires = int(time.time() + expires_seconds)
        payload = {"path": file_path, "user_id": str(user_id), "expires": expires}
        signature = self._build_signature(file_path=file_path, user_id=str(user_id), expires=expires)
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("utf-8")
        token = f"{payload_b64}.{signature}"
        filename = Path(file_path).name
        return f"{settings.base_url}/media/ads/{filename}?token={token}"

    def verify_signed_token(self, token: str, file_path: str, user_id: UUID) -> bool:
        try:
            payload_part, signature_part = token.split(".", 1)
            payload_json = base64.urlsafe_b64decode(payload_part.encode("utf-8")).decode("utf-8")
            payload = json.loads(payload_json)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return False

        expires = payload.get("expires")
        token_path = payload.get("path")
        token_user_id = payload.get("user_id")
        if not isinstance(expires, int) or not isinstance(token_path, str) or not isinstance(token_user_id, str):
            return False
        if int(time.time()) > expires:
            return False
        if token_path != file_path or token_user_id != str(user_id):
            return False

        expected = self._build_signature(file_path=token_path, user_id=token_user_id, expires=expires)
        return hmac.compare_digest(expected, signature_part)

    def absolute_path_for_media(self, file_path: str) -> Path:
        relative_path = Path(file_path.removeprefix("/media/"))
        return self.base_dir / relative_path

    @staticmethod
    def _build_signature(file_path: str, user_id: str, expires: int) -> str:
        message = f"{file_path}:{user_id}:{expires}".encode("utf-8")
        return hmac.new(settings.secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()
