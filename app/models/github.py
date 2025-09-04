from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class GitHubRepo(BaseModel):
    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    private: bool
    html_url: str
    clone_url: str
    ssh_url: str
    default_branch: str
    language: Optional[str] = None
    stargazers_count: int = 0
    forks_count: int = 0
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None


class GitHubCommit(BaseModel):
    sha: str
    message: str
    author_name: str
    author_email: str
    date: datetime
    html_url: str


class GitHubBranch(BaseModel):
    name: str
    commit_sha: str
    protected: bool = False


class GitHubFile(BaseModel):
    name: str
    path: str
    sha: str
    size: int
    type: str  # "file" or "dir"
    download_url: Optional[str] = None
    html_url: str


class GitHubCreateFileRequest(BaseModel):
    path: str
    message: str
    content: str  # Base64 encoded
    branch: Optional[str] = None


class GitHubUpdateFileRequest(BaseModel):
    path: str
    message: str
    content: str  # Base64 encoded
    sha: str  # Current file SHA
    branch: Optional[str] = None


class GitHubCreateRepoRequest(BaseModel):
    name: str
    description: Optional[str] = None
    private: bool = False
    auto_init: bool = True
    gitignore_template: Optional[str] = None
    license_template: Optional[str] = None


class GitHubPullRequest(BaseModel):
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str
    html_url: str
    head_branch: str
    base_branch: str
    created_at: datetime
    updated_at: datetime


class GitHubIssue(BaseModel):
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str
    html_url: str
    created_at: datetime
    updated_at: datetime


class GitHubUserStats(BaseModel):
    """Statistics for a GitHub user"""
    public_repos: int
    public_gists: int
    followers: int
    following: int
    total_private_repos: Optional[int] = None
    owned_private_repos: Optional[int] = None


class GitHubRateLimit(BaseModel):
    """GitHub API rate limit information"""
    limit: int
    remaining: int
    reset: datetime
    used: int
