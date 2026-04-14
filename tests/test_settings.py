from influence_trader.core.config import Settings


def test_settings_parse_comma_separated_handles_from_env(monkeypatch) -> None:
    monkeypatch.setenv("X_DEFAULT_HANDLES", "realDonaldTrump,elonmusk,jeromepowell")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.x_default_handles == [
        "realDonaldTrump",
        "elonmusk",
        "jeromepowell",
    ]


def test_settings_parse_comma_separated_keywords_from_env(monkeypatch) -> None:
    monkeypatch.setenv("RELEVANCE_KEYWORDS", "tariff,sanction,interest rate")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.relevance_keywords == [
        "tariff",
        "sanction",
        "interest rate",
    ]
