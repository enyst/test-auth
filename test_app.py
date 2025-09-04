#!/usr/bin/env python3
"""
Test script to demonstrate the FastAPI Multi-Mode Authentication App
"""

import asyncio
import httpx
import os
from app.core.config import settings

async def test_app():
    """Test the application endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing FastAPI Multi-Mode Authentication App")
    print(f"📋 Mode: {settings.app_mode}")
    print(f"🔐 Auth Required: {settings.requires_auth}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Test root endpoint
        print("1. Testing root endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 Response: {response.json()}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test health check
        print("2. Testing health check...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 Response: {response.json()}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test config endpoint
        print("3. Testing config endpoint...")
        try:
            response = await client.get(f"{base_url}/config")
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 Response: {response.json()}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test auth status
        print("4. Testing auth status...")
        try:
            response = await client.get(f"{base_url}/api/v1/auth/status")
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 Response: {response.json()}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test GitHub endpoints (without token)
        print("5. Testing GitHub repos endpoint (no token)...")
        try:
            response = await client.get(f"{base_url}/api/v1/github/repos")
            print(f"   ✅ Status: {response.status_code}")
            if response.status_code == 200:
                repos = response.json()
                print(f"   📄 Found {len(repos)} repositories")
            else:
                print(f"   📄 Response: {response.json()}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test GitHub rate limit
        print("6. Testing GitHub rate limit...")
        try:
            response = await client.get(f"{base_url}/api/v1/github/rate_limit")
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 Response: {response.json()}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test users endpoint (MU mode only)
        if settings.app_mode.value == "multi_user":
            print("7. Testing users endpoint (MU mode)...")
            try:
                response = await client.get(f"{base_url}/api/v1/users/")
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📄 Response: {response.json()}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print("7. Skipping users endpoint (not in MU mode)")
        
        print()
        print("🎉 Test completed!")


if __name__ == "__main__":
    asyncio.run(test_app())