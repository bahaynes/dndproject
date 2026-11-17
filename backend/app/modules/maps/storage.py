"""Storage backends for baked map layer images (local disk for dev, GCS for Cloud Run)."""

from pathlib import Path
from typing import Protocol

from ...config import get_settings


class MapLayerStorage(Protocol):
    """Protocol for persisting and retrieving raster map layers."""

    def put_bytes(self, key: str, data: bytes, content_type: str = "image/png") -> str:
        """Persist raw bytes under ``key`` and return the stored key."""
        ...

    def get_bytes(self, key: str) -> bytes | None:
        """Retrieve raw bytes for ``key``, or None if missing."""
        ...


class LocalMapLayerStorage:
    """Stores map layer images on the local filesystem."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir).resolve()

    def _resolve_key(self, key: str) -> Path:
        clean_key = key.lstrip("/")
        target = (self.base_dir / clean_key).resolve()
        if self.base_dir not in target.parents and target != self.base_dir:
            raise ValueError(f"Invalid storage key: {key}")
        return target

    def put_bytes(self, key: str, data: bytes, content_type: str = "image/png") -> str:
        target = self._resolve_key(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return key

    def get_bytes(self, key: str) -> bytes | None:
        target = self._resolve_key(key)
        if not target.is_file():
            return None
        return target.read_bytes()


class GCSMapLayerStorage:
    """Stores map layer images in a Google Cloud Storage bucket."""

    def __init__(self, bucket_name: str, env_prefix: str = "production") -> None:
        from google.cloud import storage  # Lazy import for local dev compatibility

        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.env_prefix = env_prefix

    def _prefixed(self, key: str) -> str:
        clean = key.lstrip("/")
        return f"{self.env_prefix}/{clean}" if not clean.startswith(f"{self.env_prefix}/") else clean

    def put_bytes(self, key: str, data: bytes, content_type: str = "image/png") -> str:
        full_key = self._prefixed(key)
        blob = self.bucket.blob(full_key)
        blob.upload_from_string(data, content_type=content_type)
        return full_key

    def get_bytes(self, key: str) -> bytes | None:
        blob = self.bucket.blob(key)
        if not blob.exists():
            return None
        return blob.download_as_bytes()


def get_layer_storage() -> MapLayerStorage:
    """Return the configured map layer storage backend."""
    settings = get_settings()
    if settings.TILE_STORAGE_BACKEND == "gcs" and settings.GCS_TILE_BUCKET:
        return GCSMapLayerStorage(
            bucket_name=settings.GCS_TILE_BUCKET,
            env_prefix=settings.APP_ENV,
        )
    return LocalMapLayerStorage(base_dir=settings.LOCAL_TILE_DIR)
