import pytest
from playwright.sync_api import Page, expect

from utils.github_mock import GithubMockUtilityClient, User


def logout(page: Page) -> None:
    page.goto('http://localhost:8000/app')
    logout_link = page.get_by_role('link', name='Logout')
    if logout_link.is_visible():
        logout_link.click()


@pytest.mark.parametrize(
    'user',
    [
        User(name='Jack', login='jack'),
        User(name='Jill', login='jill'),
    ]
)
def test_login(page: Page, login_url: str, logout_url: str, github_mock_utility: GithubMockUtilityClient, user: User) -> None:
    """
    Test that login is working as expected.

    Multiple users should be able to log in and the dashboard should change content based on the authenticated user.
    """
    logout(page)  # Ensure we start with fresh state

    github_mock_utility.store_upcoming_user(user=user)

    page.goto(login_url)

    expect(page.get_by_text('Sign in with Github')).to_be_visible()

    page.get_by_role('button', name='Sign in with Github').click()
    expect(page).to_have_title('Dashboard | Elekto')
    expect(page.get_by_text(f'Welcome! {user.name}')).to_be_visible()
    logout(page)
