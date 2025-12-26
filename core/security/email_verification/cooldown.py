# core/security/email_verification/cooldown.py
from django.core.cache import cache
import hashlib


COOLDOWN_SECONDS = 60 * 30  # 30 分鐘

def _generate_key(identifier, action: str) -> str:
    """
    內建私有函數：
    1. 統一把 identifier 轉為字串
    2. 進行 SHA256 加密防止明文外洩
    3. 加上 action 前綴
    """
    ident_str = str(identifier).strip().lower()
    
    # 使用 SHA256 雜湊處理 identifier
    hashed_ident = hashlib.sha256(ident_str.encode()).hexdigest()
    
    return f"limit:{action}:{hashed_ident}"


def is_cooldown(identifier, action: str):
    key = _generate_key(identifier, action)
    return bool(cache.get(key))


def mark_sent(identifier, action: str):
    key = _generate_key(identifier, action)

    timeout = COOLDOWN_SECONDS
        
    cache.set(key, True, timeout=timeout)