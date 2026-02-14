import os
from typing import Literal

from pydantic import BaseModel, HttpUrl

ELEKTO_HOST = os.environ.get('ELEKTO_HOST', 'localhost')
ELEKTO_PORT = os.environ.get('ELEKTO_PORT', '8000')


class AuthorizeQueryParams(BaseModel):
    client_id: str
    response_type: Literal['code']
    scope: str
    state: str
    redirect_uri: HttpUrl = f'http://{ELEKTO_HOST}:{ELEKTO_PORT}/oauth/github/callback'


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str
    scope: str


class UserResponse(BaseModel):
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    user_view_type: str
    site_admin: bool
    name: str
    company: str
    blog: str
    location: str
    email: str | None
    hireable: bool | None
    bio: str | None
    twitter_username: str | None
    notification_email: str | None
    public_repos: int
    public_gists: int
    followers: int
    following: int
    created_at: str
    updated_at: str


class UpcomingUser(BaseModel):
    name: str
    login: str
