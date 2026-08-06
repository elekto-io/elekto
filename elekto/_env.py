import os
from dotenv import load_dotenv, set_key

is_testing = os.getenv('TESTING') or "PYTEST_VERSION" in os.environ
target_env = ".env.testing" if is_testing else ".env"
load_dotenv(os.path.join(os.path.dirname(__file__), '..', target_env), override=True)


def str_to_bool(value: str) -> bool:
    value = value.lower()
    if value in ("y", "yes", "on", "1", "true", "t"):
        return True
    return False


def generate_app_key() -> None:
    key = os.urandom(32).hex()
    set_key(target_env, "APP_KEY", key)


def env(key: str, default=None):
    """Read an env var, treating an empty value as unset.

    .env.example ships blank keys (APP_KEY=, MIN_PASSCODE_LENGTH=), so an empty
    value has to fall back to the default rather than yield an empty string.
    """
    value = os.getenv(key)
    return default if not value else value
