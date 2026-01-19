from django.core.cache import cache

# 結帳熔斷器（User-based Circuit Breaker）
class CheckoutRateLimiter:
    MAX_FAIL = 3

    @classmethod
    def _get_user_key(cls, user_id):               #產生一個專屬的 cache key 標籤
        return f"checkout_fail_user:{user_id}"

    @classmethod
    def is_blocked(cls, user_id):
        """
        檢查此使用者是否已被鎖結帳
        True  = 已被鎖
        False = 尚可使用
        """
        key = cls._get_user_key(user_id)
        return cache.get(key, 0) >= cls.MAX_FAIL

    @classmethod
    def increase_fail(cls, user_id):
        """
        結帳失敗次數 +1
        """
        key = cls._get_user_key(user_id)                    # 產生使用者cache key標籤
        count = cache.get(key, 0)                           # 用標籤查到專屬cache，找出value 存進變數 count，如果沒有，就預設 0
        cache.set(key, count + 1)         # 設定專屬cache， value +1再寫回去， 60分後如果沒更新，就自動刪掉

    @classmethod
    def clear(cls, user_id):
        """
        結帳成功後清除失敗紀錄
        """
        key = cls._get_user_key(user_id)
        cache.delete(key)
