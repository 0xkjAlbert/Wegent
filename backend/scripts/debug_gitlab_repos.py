#!/usr/bin/env python3
"""
Debug GitLab API call to see why repositories are not showing

This script simulates what Wegent backend does when fetching repositories
"""

import requests
import json

def test_gitlab_repos_api(git_domain: str, token: str):
    """
    Test the exact API call that Wegent makes to fetch GitLab repositories
    """

    # Build API base URL
    if not git_domain.startswith("http://") and not git_domain.startswith("https://"):
        git_domain = f"https://{git_domain}"

    api_base_url = f"{git_domain}/api/v4"

    print("="*70)
    print("🔍 Testing GitLab Repositories API (Wegent Backend Call)")
    print("="*70)
    print(f"📍 GitLab Domain: {git_domain}")
    print(f"🔑 API Base URL: {api_base_url}")
    print()

    # Test with both authentication methods (like Wegent does)
    headers_bearer = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    headers_private_token = {
        "Private-Token": token,
        "Accept": "application/json"
    }

    # Parameters used by Wegent
    params = {
        "per_page": 100,
        "page": 1,
        "order_by": "last_activity_at",
        "membership": "true"
    }

    print("📤 API Request:")
    print(f"   URL: {api_base_url}/projects")
    print(f"   Method: GET")
    print(f"   Params: {json.dumps(params, indent=6)}")
    print()

    # Try Bearer token first
    print("1️⃣  Trying with Bearer token...")
    try:
        response = requests.get(
            f"{api_base_url}/projects",
            headers=headers_bearer,
            params=params,
            timeout=10
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            repos = response.json()
            print(f"   ✅ Success! Found {len(repos)} repositories")

            if repos:
                print("\n   📦 Sample Repositories:")
                for i, repo in enumerate(repos[:3], 1):
                    print(f"   {i}. {repo.get('path_with_namespace')}")
                    print(f"      ID: {repo.get('id')}")
                    print(f"      HTTP URL: {repo.get('http_url_to_repo')}")
                    print(f"      Visibility: {repo.get('visibility')}")
                    print()

                # Show what Wegent would extract
                print("   📋 Wegent Repository Format:")
                first_repo = repos[0]
                print(f"   {{")
                print(f"      \"id\": {first_repo.get('id')},")
                print(f"      \"name\": \"{first_repo.get('name')}\",")
                print(f"      \"full_name\": \"{first_repo.get('path_with_namespace')}\",")
                print(f"      \"clone_url\": \"{first_repo.get('http_url_to_repo')}\",")
                print(f"      \"git_domain\": \"{git_domain.replace('https://', '')}\",")
                print(f"      \"type\": \"gitlab\",")
                print(f"      \"private\": {first_repo.get('visibility') == 'private'}")
                print(f"   }}")

            else:
                print("   ⚠️  No repositories found")
                print("   This means you are not a member of any projects on this GitLab instance.")

            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Try Private-Token header (GitLab alternative)
    print("\n2️⃣  Trying with Private-Token header...")
    try:
        response = requests.get(
            f"{api_base_url}/projects",
            headers=headers_private_token,
            params=params,
            timeout=10
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            repos = response.json()
            print(f"   ✅ Success! Found {len(repos)} repositories")
            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python debug_gitlab_repos.py <gitlab_domain> <token>")
        print()
        print("Example:")
        print("  python debug_gitlab_repos.py git.53zaixian.com glpat-xxxxx")
        sys.exit(1)

    git_domain = sys.argv[1]
    token = sys.argv[2]

    success = test_gitlab_repos_api(git_domain, token)

    print("\n" + "="*70)
    if success:
        print("✅ GitLab API is working correctly!")
        print("If repositories still don't show in Wegent, check:")
        print("  1. Browser console for errors (F12 -> Console)")
        print("  2. Network tab for failed requests (F12 -> Network)")
        print("  3. Backend logs: docker-compose logs backend")
    else:
        print("❌ GitLab API test failed")
        print("Please check:")
        print("  1. Token is correct and has 'api' scope")
        print("  2. You are a member of at least one project")
        print("  3. Network connectivity to GitLab")
    print("="*70)

    sys.exit(0 if success else 1)
