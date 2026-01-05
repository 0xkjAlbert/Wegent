#!/usr/bin/env python3
"""
Quick GitLab API Test Script

Usage:
    python quick_gitlab_test.py <gitlab_domain> <token>

Example:
    python quick_gitlab_test.py git.53zaixian.com glpat-xxxxx
"""

import sys
import json
import requests

def test_gitlab_api(domain: str, token: str):
    """Quick test of GitLab API"""

    # Add https:// if not present
    if not domain.startswith("http"):
        domain = f"https://{domain}"

    api_base = f"{domain}/api/v4"
    headers = {"PRIVATE-TOKEN": token}

    print(f"🔍 Testing GitLab API: {domain}")
    print("=" * 60)

    # Test 1: Get user info
    print("\n1️⃣  Testing Token (Get User Info)...")
    try:
        response = requests.get(f"{api_base}/user", headers=headers, timeout=10)
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Token Valid!")
            print(f"   Name: {user.get('name')}")
            print(f"   Username: {user.get('username')}")
            print(f"   Email: {user.get('email')}")
        else:
            print(f"❌ Token Invalid! Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    # Test 2: List projects
    print("\n2️⃣  Testing Projects API (membership=true)...")
    try:
        params = {
            "membership": "true",
            "per_page": 5,
            "order_by": "last_activity_at"
        }
        response = requests.get(
            f"{api_base}/projects",
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            projects = response.json()
            print(f"✅ API Works! Found {len(projects)} projects")

            if projects:
                print("\n   📦 Sample Projects:")
                for i, p in enumerate(projects[:3], 1):
                    print(f"   {i}. {p.get('name_with_namespace')}")
                    print(f"      ID: {p.get('id')}")
                    print(f"      URL: {p.get('http_url_to_repo')}")
                    print(f"      SSH: {p.get('ssh_url_to_repo')}")
                    print()
            else:
                print("   ⚠️  You are not a member of any projects")
        else:
            print(f"❌ API Failed! Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    # Test 3: Check GitLab version
    print("3️⃣  Checking GitLab Version...")
    try:
        response = requests.get(f"{api_base}/version", headers=headers, timeout=10)
        if response.status_code == 200:
            version = response.json()
            print(f"✅ Version: {version.get('version', 'Unknown')}")
            print(f"   Revision: {version.get('revision', 'Unknown')}")
        else:
            print("⚠️  Cannot determine version")
    except Exception as e:
        print(f"⚠️  Version check failed: {e}")

    print("\n" + "=" * 60)
    print("✅ All tests passed! GitLab API is working.")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python quick_gitlab_test.py <gitlab_domain> <token>")
        print()
        print("Example:")
        print("  python quick_gitlab_test.py git.53zaixian.com glpat-xxxxx")
        sys.exit(1)

    domain = sys.argv[1]
    token = sys.argv[2]

    success = test_gitlab_api(domain, token)
    sys.exit(0 if success else 1)
