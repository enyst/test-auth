from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.core.auth.dependencies import get_github_token, get_current_user
from app.services.github_service import GitHubService
from app.models.github import (
    GitHubRepo, GitHubCommit, GitHubBranch, GitHubFile,
    GitHubCreateRepoRequest, GitHubRateLimit, GitHubUserStats
)
from app.models.user import User, GitHubUser

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/user", response_model=GitHubUser)
async def get_github_user(
    username: Optional[str] = None,
    github_token: Optional[str] = Depends(get_github_token)
):
    """Get GitHub user information"""
    
    if not github_token and username:
        # Public user info doesn't require token
        service = GitHubService()
        return await service.get_user(username)
    
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub token required for authenticated user info"
        )
    
    service = GitHubService(github_token)
    
    if username:
        return await service.get_user(username)
    else:
        return await service.get_authenticated_user()


@router.get("/user/stats", response_model=GitHubUserStats)
async def get_user_stats(
    username: Optional[str] = None,
    github_token: Optional[str] = Depends(get_github_token)
):
    """Get GitHub user statistics"""
    
    service = GitHubService(github_token)
    return await service.get_user_stats(username)


@router.get("/repos", response_model=List[GitHubRepo])
async def get_repositories(
    username: Optional[str] = None,
    type: str = Query("all", description="Repository type: all, owner, member"),
    sort: str = Query("updated", description="Sort by: created, updated, pushed, full_name"),
    per_page: int = Query(30, le=100, description="Results per page"),
    github_token: Optional[str] = Depends(get_github_token)
):
    """Get repositories for a user"""
    
    service = GitHubService(github_token)
    return await service.get_user_repos(username, type, sort, per_page)


@router.get("/repos/{owner}/{repo}", response_model=GitHubRepo)
async def get_repository(
    owner: str,
    repo: str,
    github_token: Optional[str] = Depends(get_github_token)
):
    """Get repository information"""
    
    service = GitHubService(github_token)
    return await service.get_repo(owner, repo)


@router.post("/repos", response_model=GitHubRepo)
async def create_repository(
    repo_data: GitHubCreateRepoRequest,
    github_token: str = Depends(get_github_token)
):
    """Create a new repository"""
    
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token required to create repositories"
        )
    
    service = GitHubService(github_token)
    return await service.create_repo(repo_data)


@router.delete("/repos/{owner}/{repo}")
async def delete_repository(
    owner: str,
    repo: str,
    github_token: str = Depends(get_github_token)
):
    """Delete a repository"""
    
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token required to delete repositories"
        )
    
    service = GitHubService(github_token)
    success = await service.delete_repo(owner, repo)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete repository"
        )
    
    return {"message": f"Repository {owner}/{repo} deleted successfully"}


@router.get("/repos/{owner}/{repo}/contents", response_model=List[GitHubFile])
async def get_repository_contents(
    owner: str,
    repo: str,
    path: str = Query("", description="Path within repository"),
    ref: Optional[str] = Query(None, description="Branch or commit SHA"),
    github_token: Optional[str] = Depends(get_github_token)
):
    """Get repository contents"""
    
    service = GitHubService(github_token)
    return await service.get_repo_contents(owner, repo, path, ref)


@router.get("/repos/{owner}/{repo}/contents/{path:path}/raw")
async def get_file_content(
    owner: str,
    repo: str,
    path: str,
    ref: Optional[str] = Query(None, description="Branch or commit SHA"),
    github_token: Optional[str] = Depends(get_github_token)
):
    """Get raw file content"""
    
    service = GitHubService(github_token)
    content = await service.get_file_content(owner, repo, path, ref)
    
    return {"content": content, "path": path}


@router.put("/repos/{owner}/{repo}/contents/{path:path}")
async def create_or_update_file(
    owner: str,
    repo: str,
    path: str,
    message: str,
    content: str,
    sha: Optional[str] = None,
    branch: Optional[str] = None,
    github_token: str = Depends(get_github_token)
):
    """Create or update a file in repository"""
    
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token required to modify files"
        )
    
    service = GitHubService(github_token)
    result = await service.create_or_update_file(
        owner, repo, path, message, content, sha, branch
    )
    
    return result


@router.get("/repos/{owner}/{repo}/branches", response_model=List[GitHubBranch])
async def get_branches(
    owner: str,
    repo: str,
    github_token: Optional[str] = Depends(get_github_token)
):
    """Get repository branches"""
    
    service = GitHubService(github_token)
    return await service.get_branches(owner, repo)


@router.post("/repos/{owner}/{repo}/branches")
async def create_branch(
    owner: str,
    repo: str,
    branch_name: str,
    from_sha: str,
    github_token: str = Depends(get_github_token)
):
    """Create a new branch"""
    
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token required to create branches"
        )
    
    service = GitHubService(github_token)
    success = await service.create_branch(owner, repo, branch_name, from_sha)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create branch"
        )
    
    return {"message": f"Branch {branch_name} created successfully"}


@router.get("/repos/{owner}/{repo}/commits", response_model=List[GitHubCommit])
async def get_commits(
    owner: str,
    repo: str,
    sha: Optional[str] = Query(None, description="Branch or commit SHA"),
    path: Optional[str] = Query(None, description="Filter by file path"),
    per_page: int = Query(30, le=100, description="Results per page"),
    github_token: Optional[str] = Depends(get_github_token)
):
    """Get repository commits"""
    
    service = GitHubService(github_token)
    return await service.get_commits(owner, repo, sha, path, per_page)


@router.get("/rate_limit", response_model=GitHubRateLimit)
async def get_rate_limit(
    github_token: Optional[str] = Depends(get_github_token)
):
    """Get GitHub API rate limit status"""
    
    service = GitHubService(github_token)
    return await service.get_rate_limit()