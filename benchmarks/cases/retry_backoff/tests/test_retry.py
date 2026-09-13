from retry import retry_delays


def test_schedule_starts_at_base() -> None:
    assert retry_delays(1, 4) == [1, 2, 4, 8]
    assert retry_delays(3, 0) == []
