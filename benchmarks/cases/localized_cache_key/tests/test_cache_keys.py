from cache_keys import profile_cache_key


def test_locale_is_part_of_key() -> None:
    assert profile_cache_key(42, "en-US") == "profile:42:en-us"
    assert profile_cache_key(42, "pt-BR") != profile_cache_key(42, "en-US")
