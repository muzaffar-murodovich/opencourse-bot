from telegram.error import BadRequest, Forbidden

import broadcast_core


def test_is_blocked_true_for_forbidden():
    assert broadcast_core._is_blocked(Forbidden("bot was blocked by the user")) is True


def test_is_blocked_false_for_other_errors():
    assert broadcast_core._is_blocked(BadRequest("chat not found")) is False
    assert broadcast_core._is_blocked(ValueError("x")) is False


def test_send_delay_under_telegram_cap():
    # Must stay under Telegram's ~30 msg/s bulk limit.
    assert broadcast_core.MESSAGES_PER_SECOND <= 30
    assert broadcast_core.SEND_DELAY_SECONDS >= 1.0 / 30
