import pytest

from utils.github_mock.client import GithubMockUtilityClient


@pytest.fixture
def host() -> str:
    return 'http://localhost:8000'


@pytest.fixture
def login_url(host: str) -> str:
    return f'{host}/login'


@pytest.fixture
def logout_url(host: str) -> str:
    return f'{host}/logout'


@pytest.fixture
def app_url(host: str) -> str:
    return f'{host}/app'


@pytest.fixture
def github_mock_host() -> str:
    return 'http://localhost:9000'


@pytest.fixture
def github_mock_utility(github_mock_host: str) -> GithubMockUtilityClient:
    return GithubMockUtilityClient(host=github_mock_host)
