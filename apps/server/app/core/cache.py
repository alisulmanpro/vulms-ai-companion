import logging
import os
import threading
from pathlib import Path
from typing import Any, Optional
from cachetools import TTLCache

logger = logging.getLogger("VULMS_Server")

_DEFAULT_DISK_DIR = os.getenv("APP_CACHE_DIR", "./app_cache_data")


class HybridCacheManager:
    def __init__(
        self,
        ram_maxsize: int = 200,
        ram_ttl: int = 300,
        disk_dir: Optional[str] = None,
        disk_size_limit: int = 1_073_741_824,
    ):
        self.l1_ram = TTLCache(maxsize=ram_maxsize, ttl=ram_ttl)
        self.l2_disk = None

        cache_path = Path(disk_dir or _DEFAULT_DISK_DIR).resolve()
        try:
            from diskcache import Cache

            cache_path.mkdir(parents=True, exist_ok=True)
            try:
                self.l2_disk = Cache(
                    directory=str(cache_path),
                    size_limit=disk_size_limit,
                    timeout=30.0,
                    sqlite_journal_mode="truncate",
                )
            except Exception as first_exc:
                # If stale WAL/SHM lock files exist from a crashed process, attempt cleanup & retry
                for ext in ["-wal", "-shm"]:
                    lock_file = cache_path / f"cache.db{ext}"
                    if lock_file.exists():
                        try:
                            lock_file.unlink()
                        except Exception:
                            pass
                self.l2_disk = Cache(
                    directory=str(cache_path),
                    size_limit=disk_size_limit,
                    timeout=30.0,
                    sqlite_journal_mode="truncate",
                )

            logger.info(
                "Hybrid cache initialized (RAM + L2 Disk at %s).",
                cache_path,
            )
        except Exception as exc:
            logger.warning(
                "L2 Disk cache unavailable (%s). Operating in RAM-only mode.",
                exc,
            )

    def get(self, key: str) -> Optional[Any]:
        if key in self.l1_ram:
            logger.debug(f"[L1 RAM HIT] Key: {key}")
            return self.l1_ram[key]

        if self.l2_disk is not None:
            data = self.l2_disk.get(key)
            if data is not None:
                logger.debug(f"[L2 DISK HIT] Key: {key} -> Elevating to L1 RAM")
                self.l1_ram[key] = data
                return data

        logger.debug(f"[CACHE MISS] Key: {key}")
        return None

    def set(self, key: str, value: Any, expire_seconds: int = 600) -> None:
        self.l1_ram[key] = value
        if self.l2_disk is not None:
            self.l2_disk.set(key, value, expire=expire_seconds)
        logger.debug(f"[CACHE STORED] Key: {key} (TTL: {expire_seconds}s)")

    def delete(self, key: str) -> None:
        if key in self.l1_ram:
            del self.l1_ram[key]
        if self.l2_disk is not None:
            self.l2_disk.delete(key)

    def clear(self) -> None:
        self.l1_ram.clear()
        if self.l2_disk is not None:
            self.l2_disk.clear()


_cache_manager: Optional[HybridCacheManager] = None
_cache_lock = threading.Lock()


def get_cache_manager() -> HybridCacheManager:
    global _cache_manager
    if _cache_manager is None:
        with _cache_lock:
            if _cache_manager is None:
                _cache_manager = HybridCacheManager()
    return _cache_manager


cache_manager: HybridCacheManager
_cache_proxy_attrs = ("get", "set", "delete", "clear")


class _CacheProxy:
    def __getattr__(self, item):
        return getattr(get_cache_manager(), item)

    def __setattr__(self, key, value):
        setattr(get_cache_manager(), key, value)


cache_manager = _CacheProxy()  # type: ignore[assignment]
