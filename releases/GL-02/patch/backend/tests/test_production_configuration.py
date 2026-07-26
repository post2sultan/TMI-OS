import unittest

from pydantic import SecretStr

from app.core.settings import Settings


def production_settings(**overrides) -> Settings:
    values = {
        "APP_ENV": "production",
        "POSTGRES_PASSWORD": SecretStr("strong-postgres-secret"),
        "QDRANT_API_KEY": SecretStr("strong-qdrant-secret"),
        "REDIS_PASSWORD": SecretStr("strong-redis-secret"),
        "AUTH_VIEWER_API_KEY": SecretStr("strong-viewer-secret"),
        "AUTH_OPERATOR_API_KEY": SecretStr("strong-operator-secret"),
        "AUTH_REVIEWER_API_KEY": SecretStr("strong-reviewer-secret"),
        "AUTH_ADMIN_API_KEY": SecretStr("strong-admin-secret"),
    }
    values.update(overrides)
    return Settings(**values)


class ProductionConfigurationTests(unittest.TestCase):

    def test_strong_production_secrets_are_accepted(self) -> None:
        production_settings().validate_production_secrets()

    def test_placeholder_api_key_is_rejected(self) -> None:
        settings = production_settings(
            AUTH_ADMIN_API_KEY=SecretStr("REPLACE_WITH_ADMIN_SECRET")
        )
        with self.assertRaises(ValueError):
            settings.validate_production_secrets()

    def test_default_database_password_is_rejected(self) -> None:
        settings = production_settings(
            POSTGRES_PASSWORD=SecretStr("ChangeThisPassword123!")
        )
        with self.assertRaises(ValueError):
            settings.validate_production_secrets()

    def test_missing_service_secrets_are_rejected(self) -> None:
        settings = production_settings(QDRANT_API_KEY=SecretStr(""))
        with self.assertRaises(ValueError):
            settings.validate_production_secrets()


if __name__ == "__main__":
    unittest.main()

