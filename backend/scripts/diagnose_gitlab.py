#!/usr/bin/env python3
"""
GitLab Integration Diagnostic Script

This script helps diagnose GitLab integration issues with Wegent.
Compatible with GitLab 9.6+
"""

import sys
import requests
from typing import Dict, Any

def test_gitlab_connection(git_domain: str, token: str) -> Dict[str, Any]:
    """
    Test GitLab API connection and permissions

    Args:
        git_domain: GitLab domain (e.g., gitlab.com or custom domain)
        token: GitLab Personal Access Token

    Returns:
        Diagnostic results
    """
    results = {
        "success": False,
        "gitlab_version": None,
        "api_accessible": False,
        "token_valid": False,
        "projects_accessible": False,
        "errors": []
    }

    # Build API base URL
    if not git_domain.startswith("http://") and not git_domain.startswith("https://"):
        git_domain = f"https://{git_domain}"

    api_base = f"{git_domain}/api/v4"

    print(f"🔍 Testing GitLab Integration")
    print(f"📍 GitLab Domain: {git_domain}")
    print(f"🔑 API Base URL: {api_base}")
    print()

    # Test 1: Check API accessibility
    print("Test 1: Checking API accessibility...")
    try:
        response = requests.get(f"{api_base}/", timeout=10)
        if response.status_code == 200:
            results["api_accessible"] = True
            print("✅ API is accessible")
        else:
            results["errors"].append(f"API returned status {response.status_code}")
            print(f"❌ API returned status {response.status_code}")
    except Exception as e:
        results["errors"].append(f"Cannot connect to API: {str(e)}")
        print(f"❌ Cannot connect to API: {str(e)}")
        return results

    # Test 2: Validate token and get user info
    print("\nTest 2: Validating token...")
    headers = {"PRIVATE-TOKEN": token}

    try:
        response = requests.get(f"{api_base}/user", headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            results["token_valid"] = True
            print(f"✅ Token is valid")
            print(f"   User: {user_data.get('name')} (@{user_data.get('username')})")
        else:
            results["errors"].append(f"Token validation failed: {response.status_code}")
            print(f"❌ Token validation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return results
    except Exception as e:
        results["errors"].append(f"Token validation error: {str(e)}")
        print(f"❌ Token validation error: {str(e)}")
        return results

    # Test 3: Check GitLab version
    print("\nTest 3: Checking GitLab version...")
    try:
        response = requests.get(f"{api_base}/version", headers=headers, timeout=10)
        if response.status_code == 200:
            version_data = response.json()
            results["gitlab_version"] = version_data.get("version")
            print(f"✅ GitLab Version: {results['gitlab_version']}")
        else:
            print(f"⚠️  Cannot determine version (status {response.status_code})")
    except Exception as e:
        print(f"⚠️  Cannot check version: {str(e)}")

    # Test 4: Check /projects endpoint with membership parameter
    print("\nTest 4: Testing /projects endpoint with membership=true...")
    try:
        params = {
            "membership": "true",
            "per_page": "1",
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
            results["projects_accessible"] = True
            print(f"✅ Projects endpoint works!")
            print(f"   Found {len(projects)} project(s)")

            if projects:
                project = projects[0]
                print(f"\n📦 Sample Project:")
                print(f"   Name: {project.get('name_with_namespace')}")
                print(f"   URL: {project.get('http_url_to_repo')}")
                print(f"   ID: {project.get('id')}")
        else:
            results["errors"].append(
                f"Projects endpoint failed: {response.status_code}"
            )
            print(f"❌ Projects endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        results["errors"].append(f"Projects endpoint error: {str(e)}")
        print(f"❌ Projects endpoint error: {str(e)}")

    # Final result
    results["success"] = (
        results["api_accessible"] and
        results["token_valid"] and
        results["projects_accessible"]
    )

    return results


def main():
    if len(sys.argv) < 3:
        print("Usage: python diagnose_gitlab.py <git_domain> <token>")
        print()
        print("Example:")
        print("  python diagnose_gitlab.py gitlab.com glpat-xxxxxxxxxxxx")
        print("  python diagnose_gitlab.py git.example.com glpat-xxxxxxxxxxxx")
        sys.exit(1)

    git_domain = sys.argv[1]
    token = sys.argv[2]

    results = test_gitlab_connection(git_domain, token)

    print("\n" + "="*60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*60)

    if results["success"]:
        print("✅ All tests passed!")
        print("\nYour GitLab integration should work correctly with Wegent.")
    else:
        print("❌ Some tests failed. Please check the following:")
        print()

        if not results["api_accessible"]:
            print("• API is not accessible")
            print("  → Check if GitLab URL is correct")
            print("  → Check network/firewall settings")

        if not results["token_valid"]:
            print("• Token is invalid")
            print("  → Verify token has 'api' scope")
            print("  → Check if token has expired")

        if not results["projects_accessible"]:
            print("• Cannot access projects")
            print("  → Verify token permissions")
            print("  → Check if user is a member of any projects")

        if results["errors"]:
            print("\n📋 Errors:")
            for error in results["errors"]:
                print(f"  • {error}")

    print()
    print(f"GitLab Version: {results['gitlab_version'] or 'Unknown'}")
    print()

    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
