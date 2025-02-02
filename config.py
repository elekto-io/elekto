import os
from utils import env

def strtobool(value: str) -> bool:
  value = value.lower()
  if value in ("y", "yes", "on", "1", "true", "t"):
    return True
  return False


class BaseConfig:
    """Base configuration shared across all environments."""
    
    NAME = env("APP_NAME", "k8s.elections")

    SECRET_KEY = env("APP_KEY", "test")

    DEBUG = bool(strtobool(env("APP_DEBUG", "False")))

    # Template Auto Reload
    TEMPLATES_AUTO_RELOAD = DEBUG

    META = {
        "REMOTE": env("META_REPO"),
        "ELECDIR": env("ELECTION_DIR"),
        "PATH": env("META_PATH", "meta"),
        "DEPLOYMENT": env("META_DEPLOYMENT", "local"),
        "BRANCH": env("META_BRANCH", "main"),
        "SECRET": env("META_SECRET"),
    }

    GITHUB = {
        "client_id": env("GITHUB_CLIENT_ID"),
        "client_secret": env("GITHUB_CLIENT_SECRET"),
        "redirect": env("GITHUB_REDIRECT", "/oauth/github/callback"),
        "scope": "user:login,name",
    }

    PASSCODE_LENGTH = int(env("MIN_PASSCODE_LENGTH", 6))


class ProductionConfig(BaseConfig):
    """Configuration for Production Environment."""
    
    DEBUG = False

    # Database Connection (Use the current DB settings)
    if env("DB_CONNECTION") == "mysql":
        DATABASE_URL = "mysql://{user}:{password}@{host}:{port}/{dbname}".format(
            user=env("DB_USERNAME", "root"),
            password=env("DB_PASSWORD", ""),
            host=env("DB_HOST", "localhost"),
            port=env("DB_PORT", 3306),
            dbname=env("DB_DATABASE"),
        )
    elif env("DB_CONNECTION") == "postgresql":
        DATABASE_URL = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
            user=env("DB_USERNAME", "root"),
            password=env("DB_PASSWORD", ""),
            host=env("DB_HOST", "localhost"),
            port=env("DB_PORT", 5432),
            dbname=env("DB_DATABASE"),
        )
    else:
        raise ValueError("Invalid DB engine for production!")


class TestingConfig(BaseConfig):
    """Configuration for Testing Environment."""
    
    TESTING = True
    DEBUG = True

    DATABASE_URL = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
        user=env("TEST_DB_USERNAME", "root"),
        password=env("TEST_DB_PASSWORD", ""),
        host=env("TEST_DB_HOST", "localhost"),
        port=env("TEST_DB_PORT", 5432),
        dbname=env("TEST_DB_DATABASE"),
    )
