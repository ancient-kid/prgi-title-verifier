"""
Pending Application Lock Manager

Prevents race conditions when two or more applicants apply for the same / deceptively similar title.
Uses Redis (with seamless high-speed in-memory fallback):
- Pushes title to cache with a Time-to-Live (TTL, default 10 mins).
- Prevents concurrent duplicate submissions.
- Automatically cleans up expired locks.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.config import REDIS_LOCK_TTL_SECONDS, REDIS_URL
from backend.pipeline.stage1_preprocessor import clean_text


class LockManager:
    def __init__(self, redis_url: str = REDIS_URL, default_ttl: int = REDIS_LOCK_TTL_SECONDS):
        self.default_ttl = default_ttl
        self.redis_client = None
        self.memory_locks: Dict[str, Dict[str, Any]] = {}
        
        try:
            import redis
            client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=1)
            client.ping()
            self.redis_client = client
            print("[LockManager] Connected to Redis cluster successfully.")
        except Exception:
            self.redis_client = None
            print("[LockManager] Redis not connected. Operating in high-speed In-Memory Lock mode.")

    def _get_key(self, title: str) -> str:
        clean = clean_text(title)
        return f"prgi:pending_lock:{clean}"

    def acquire_lock(
        self,
        title: str,
        applicant_id: str,
        applicant_name: str = "Anonymous",
        ttl_seconds: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Acquire lock for a title.
        Returns: (success: bool, error_message: Optional[str], lock_data: dict)
        """
        ttl = ttl_seconds or self.default_ttl
        clean_title = clean_text(title)
        key = self._get_key(clean_title)
        now = time.time()
        
        lock_data = {
            "title": title,
            "cleaned_title": clean_title,
            "applicant_id": applicant_id,
            "applicant_name": applicant_name,
            "created_at": now,
            "expires_at": now + ttl,
            "ttl_seconds": ttl
        }
        
        # 1. Redis Mode
        if self.redis_client:
            try:
                # Set if Not Exists with expiry (NX + EX)
                val_json = json.dumps(lock_data)
                acquired = self.redis_client.set(key, val_json, nx=True, ex=ttl)
                if acquired:
                    return True, None, lock_data
                else:
                    existing = self.redis_client.get(key)
                    ex_data = json.loads(existing) if existing else {}
                    ttl_rem = self.redis_client.ttl(key)
                    ex_data["ttl_remaining"] = ttl_rem
                    return False, f"Title '{title}' is currently locked by applicant '{ex_data.get('applicant_name', 'Another User')}'.", ex_data
            except Exception as e:
                print(f"[LockManager] Redis operation failed: {e}, using in-memory.")

        # 2. In-Memory Mode
        self.cleanup_expired()
        if clean_title in self.memory_locks:
            ex_data = self.memory_locks[clean_title]
            ttl_rem = max(0, int(ex_data["expires_at"] - now))
            ex_data_copy = dict(ex_data)
            ex_data_copy["ttl_remaining"] = ttl_rem
            return False, f"Title '{title}' is currently locked by applicant '{ex_data.get('applicant_name', 'Another User')}'.", ex_data_copy
            
        self.memory_locks[clean_title] = lock_data
        return True, None, lock_data

    def check_lock(self, title: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if a title is currently locked under pending application.
        Returns: (is_locked: bool, lock_info: Optional[dict])
        """
        clean_title = clean_text(title)
        key = self._get_key(clean_title)
        now = time.time()
        
        # 1. Redis Mode
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    data = json.loads(val)
                    data["ttl_remaining"] = max(0, self.redis_client.ttl(key))
                    return True, data
            except Exception as e:
                print(f"[LockManager] Redis get failed: {e}")

        # 2. In-Memory Mode
        self.cleanup_expired()
        if clean_title in self.memory_locks:
            data = self.memory_locks[clean_title]
            if data["expires_at"] > now:
                data_copy = dict(data)
                data_copy["ttl_remaining"] = max(0, int(data["expires_at"] - now))
                return True, data_copy
            else:
                del self.memory_locks[clean_title]
                
        return False, None

    def release_lock(self, title: str, applicant_id: str) -> bool:
        """Release lock if owned by applicant_id."""
        clean_title = clean_text(title)
        key = self._get_key(clean_title)
        
        # 1. Redis Mode
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    data = json.loads(val)
                    if data.get("applicant_id") == applicant_id:
                        self.redis_client.delete(key)
                        return True
            except Exception:
                pass

        # 2. In-Memory Mode
        if clean_title in self.memory_locks:
            if self.memory_locks[clean_title].get("applicant_id") == applicant_id:
                del self.memory_locks[clean_title]
                return True
        return False

    def list_active_locks(self) -> List[Dict[str, Any]]:
        """List all active locked pending titles."""
        now = time.time()
        results = []
        
        # 1. Redis Mode
        if self.redis_client:
            try:
                keys = self.redis_client.keys("prgi:pending_lock:*")
                for k in keys:
                    val = self.redis_client.get(k)
                    if val:
                        d = json.loads(val)
                        d["ttl_remaining"] = max(0, self.redis_client.ttl(k))
                        results.append(d)
                return sorted(results, key=lambda x: x.get("created_at", 0), reverse=True)
            except Exception:
                pass

        # 2. In-Memory Mode
        self.cleanup_expired()
        for k, v in self.memory_locks.items():
            if v["expires_at"] > now:
                vc = dict(v)
                vc["ttl_remaining"] = max(0, int(v["expires_at"] - now))
                results.append(vc)
                
        return sorted(results, key=lambda x: x.get("created_at", 0), reverse=True)

    def cleanup_expired(self):
        """Clean up in-memory expired entries."""
        now = time.time()
        expired_keys = [k for k, v in self.memory_locks.items() if v["expires_at"] <= now]
        for k in expired_keys:
            del self.memory_locks[k]
