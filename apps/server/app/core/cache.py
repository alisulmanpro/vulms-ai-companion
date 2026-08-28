from pathlib import Path
from typing import Any, Optional
from cachetools import TTLCache
from diskcache import Cache


class HybridCacheManager:
    def __init__(
            self,
            ram_maxsize: int = 100,
            ram_ttl: int = 300,
            disk_dir: str = "./app_cache_data",
            disk_size_limit: int = 1_073_741_824  # 1 GB
    ):
        """
        L1 (RAM) and L2 (Disk) Cache Wrapper
        """
        # L1 RAM Cache (cachetools)
        self.l1_ram = TTLCache(maxsize=ram_maxsize, ttl=ram_ttl)

        # L2 Disk Cache (diskcache)
        cache_path = Path(disk_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        self.l2_disk = Cache(directory=str(cache_path), size_limit=disk_size_limit)

    def get(self, key: str) -> Optional[Any]:
        # 1. Check L1 RAM Cache
        if key in self.l1_ram:
            print(f"[L1 RAM HIT] Key: {key}")
            return self.l1_ram[key]

        # 2. Check L2 Disk Cache
        data = self.l2_disk.get(key)
        if data is not None:
            print(f"[L2 DISK HIT] Key: {key} -> Elevating to L1 RAM")
            # Populate back to RAM for fast subsequent reads
            self.l1_ram[key] = data
            return data

        print(f"[CACHE MISS] Key: {key}")
        return None

    def set(self, key: str, value: Any, expire_seconds: int = 3600) -> None:
        """
        Save value to both RAM (L1) and Disk (L2)
        """
        # Save in L1 RAM
        self.l1_ram[key] = value

        # Save in L2 Disk with TTL
        self.l2_disk.set(key, value, expire=expire_seconds)
        print(f"[CACHE STORED] Key: {key} (L1 RAM + L2 Disk)")

    def delete(self, key: str) -> None:
        """
        Remove key from both cache layers
        """
        if key in self.l1_ram:
            del self.l1_ram[key]
        self.l2_disk.delete(key)


# Global Cache Instance Singleton
cache_manager = HybridCacheManager()
