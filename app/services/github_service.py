import base64
import httpx
from typing import List, Optional, Dict, Any
from app.models.github import (
    GitHubRepo, GitHubCommit, GitHubBranch, GitHubFile,
    GitHubCreateRepoRequest, GitHubRateLimit, GitHubUserStats
)
from app.models.user import GitHubUser


class GitHubService:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "FastAPI-Multi-Mode-App"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[Any, Any]:
        """Make HTTP request to GitHub API"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    # User Operations
    async def get_authenticated_user(self) -> GitHubUser:
        """Get the authenticated user's information"""
        if not self.token:
            raise ValueError("GitHub token required for this operation")
        
        data = await self._make_request("GET", "/user")
        return GitHubUser(**data)
    
    async def get_user(self, username: str) -> GitHubUser:
        """Get public information about a user"""
        data = await self._make_request("GET", f"/users/{username}")
        return GitHubUser(**data)
    
    async def get_user_stats(self, username: Optional[str] = None) -> GitHubUserStats:
        """Get user statistics"""
        endpoint = "/user" if not username else f"/users/{username}"
        data = await self._make_request("GET", endpoint)
        
        return GitHubUserStats(
            public_repos=data.get("public_repos", 0),
            public_gists=data.get("public_gists", 0),
            followers=data.get("followers", 0),
            following=data.get("following", 0),
            total_private_repos=data.get("total_private_repos"),
            owned_private_repos=data.get("owned_private_repos")
        )
    
    # Repository Operations
    async def get_user_repos(
        self, 
        username: Optional[str] = None,
        type: str = "all",  # all, owner, member
        sort: str = "updated",  # created, updated, pushed, full_name
        per_page: int = 30
    ) -> List[GitHubRepo]:
        """Get repositories for a user"""
        endpoint = "/user/repos" if not username else f"/users/{username}/repos"
        params = {
            "type": type,
            "sort": sort,
            "per_page": per_page
        }
        
        data = await self._make_request("GET", endpoint, params=params)
        return [GitHubRepo(**repo) for repo in data]
    
    async def get_repo(self, owner: str, repo: str) -> GitHubRepo:
        """Get repository information"""
        data = await self._make_request("GET", f"/repos/{owner}/{repo}")
        return GitHubRepo(**data)
    
    async def create_repo(self, repo_data: GitHubCreateRepoRequest) -> GitHubRepo:
        """Create a new repository"""
        if not self.token:
            raise ValueError("GitHub token required for this operation")
        
        data = await self._make_request("POST", "/user/repos", data=repo_data.dict())
        return GitHubRepo(**data)
    
    async def delete_repo(self, owner: str, repo: str) -> bool:
        """Delete a repository"""
        if not self.token:
            raise ValueError("GitHub token required for this operation")
        
        try:
            await self._make_request("DELETE", f"/repos/{owner}/{repo}")
            return True
        except httpx.HTTPStatusError:
            return False
    
    # File Operations
    async def get_repo_contents(
        self, 
        owner: str, 
        repo: str, 
        path: str = "",
        ref: Optional[str] = None
    ) -> List[GitHubFile]:
        """Get repository contents"""
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else {}
        
        data = await self._make_request("GET", endpoint, params=params)
        
        # Handle single file vs directory
        if isinstance(data, dict):
            data = [data]
        
        return [GitHubFile(**item) for item in data]
    
    async def get_file_content(
        self, 
        owner: str, 
        repo: str, 
        path: str,
        ref: Optional[str] = None
    ) -> str:
        """Get file content (decoded from base64)"""
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else {}
        
        data = await self._make_request("GET", endpoint, params=params)
        
        if data.get("type") != "file":
            raise ValueError("Path does not point to a file")
        
        content = data.get("content", "")
        return base64.b64decode(content).decode("utf-8")
    
    async def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        message: str,
        content: str,
        sha: Optional[str] = None,  # Required for updates
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update a file in repository"""
        if not self.token:
            raise ValueError("GitHub token required for this operation")
        
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        
        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8")
        }
        
        if sha:  # Update existing file
            data["sha"] = sha
        
        if branch:
            data["branch"] = branch
        
        return await self._make_request("PUT", endpoint, data=data)
    
    # Branch Operations
    async def get_branches(self, owner: str, repo: str) -> List[GitHubBranch]:
        """Get repository branches"""
        data = await self._make_request("GET", f"/repos/{owner}/{repo}/branches")
        
        return [
            GitHubBranch(
                name=branch["name"],
                commit_sha=branch["commit"]["sha"],
                protected=branch.get("protected", False)
            )
            for branch in data
        ]
    
    async def create_branch(
        self, 
        owner: str, 
        repo: str, 
        branch_name: str, 
        from_sha: str
    ) -> bool:
        """Create a new branch"""
        if not self.token:
            raise ValueError("GitHub token required for this operation")
        
        endpoint = f"/repos/{owner}/{repo}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": from_sha
        }
        
        try:
            await self._make_request("POST", endpoint, data=data)
            return True
        except httpx.HTTPStatusError:
            return False
    
    # Commit Operations
    async def get_commits(
        self, 
        owner: str, 
        repo: str, 
        sha: Optional[str] = None,
        path: Optional[str] = None,
        per_page: int = 30
    ) -> List[GitHubCommit]:
        """Get repository commits"""
        endpoint = f"/repos/{owner}/{repo}/commits"
        params = {"per_page": per_page}
        
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        
        data = await self._make_request("GET", endpoint, params=params)
        
        return [
            GitHubCommit(
                sha=commit["sha"],
                message=commit["commit"]["message"],
                author_name=commit["commit"]["author"]["name"],
                author_email=commit["commit"]["author"]["email"],
                date=commit["commit"]["author"]["date"],
                html_url=commit["html_url"]
            )
            for commit in data
        ]
    
    # Rate Limit
    async def get_rate_limit(self) -> GitHubRateLimit:
        """Get current rate limit status"""
        data = await self._make_request("GET", "/rate_limit")
        rate = data["rate"]
        
        return GitHubRateLimit(
            limit=rate["limit"],
            remaining=rate["remaining"],
            reset=rate["reset"],
            used=rate["used"]
        )
    
    # OAuth Operations (for authentication flow)
    @staticmethod
    async def exchange_code_for_token(
        client_id: str,
        client_secret: str,
        code: str
    ) -> str:
        """Exchange OAuth code for access token"""
        url = "https://github.com/login/oauth/access_token"
        
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code
        }
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "FastAPI-Multi-Mode-App"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if "access_token" not in result:
                raise ValueError(f"Failed to get access token: {result}")
            
            return result["access_token"]