from django.test import TestCase
from django.core.cache import cache
from core.security.rate_limit.limiter import CheckoutRateLimiter
from django.test import override_settings

@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class CheckoutRateLimiterTest(TestCase):

    def setUp(self):
        self.user_id = 999
        cache.clear()   # ✅ 每個測試前清空 cache，避免測試互相污染

    def test_initial_state_not_blocked(self):
        """
        ✅ 初始狀態：尚未失敗，不應被鎖
        """
        blocked = CheckoutRateLimiter.is_blocked(self.user_id)
        self.assertFalse(blocked)

    def test_increase_fail_until_blocked(self):
        """
        ✅ 失敗累積到 MAX_FAIL，應被鎖
        """
        for _ in range(CheckoutRateLimiter.MAX_FAIL - 1):
            CheckoutRateLimiter.increase_fail(self.user_id)
            self.assertFalse(CheckoutRateLimiter.is_blocked(self.user_id))

        # ✅ 第 5 次（MAX_FAIL）
        CheckoutRateLimiter.increase_fail(self.user_id)
        self.assertTrue(CheckoutRateLimiter.is_blocked(self.user_id))

    def test_clear_resets_block(self):
        """
        ✅ clear() 應重置失敗紀錄
        """
        for _ in range(CheckoutRateLimiter.MAX_FAIL):

            CheckoutRateLimiter.increase_fail(self.user_id)

        self.assertTrue(CheckoutRateLimiter.is_blocked(self.user_id))

        # ✅ 清除
        CheckoutRateLimiter.clear(self.user_id)

        self.assertFalse(CheckoutRateLimiter.is_blocked(self.user_id))

    def test_different_users_independent(self):
        """
        ✅ 不同 user 不應互相影響
        """
        user_a = 1
        user_b = 2

        for _ in range(CheckoutRateLimiter.MAX_FAIL):

            CheckoutRateLimiter.increase_fail(user_a)

        self.assertTrue(CheckoutRateLimiter.is_blocked(user_a))

        self.assertFalse(CheckoutRateLimiter.is_blocked(user_b))
