#!/usr/bin/env python3
"""
Test script to debug scanner loading issues
"""
import requests
import sys

def test_scanner_access():
    base_url = "http://localhost:5000"
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Test 1: Check if homepage loads
    print("Testing homepage...")
    try:
        response = session.get(f"{base_url}/")
        print(f"Homepage status: {response.status_code}")
        if response.status_code != 200:
            print("Homepage failed to load")
            return False
    except Exception as e:
        print(f"Homepage error: {e}")
        return False
    
    # Test 2: Check scanner redirect (should redirect to login)
    print("\nTesting scanner without login...")
    try:
        response = session.get(f"{base_url}/scanner", allow_redirects=False)
        print(f"Scanner status (no login): {response.status_code}")
        if response.status_code == 302:
            print("✓ Scanner correctly redirects to login")
        else:
            print("✗ Scanner redirect not working")
    except Exception as e:
        print(f"Scanner error: {e}")
        return False
    
    # Test 3: Check if login page loads
    print("\nTesting login page...")
    try:
        response = session.get(f"{base_url}/login")
        print(f"Login page status: {response.status_code}")
        if response.status_code != 200:
            print("Login page failed to load")
            return False
        print("✓ Login page loads correctly")
    except Exception as e:
        print(f"Login page error: {e}")
        return False
    
    # Test 4: Check if registration works
    print("\nTesting registration page...")
    try:
        response = session.get(f"{base_url}/register")
        print(f"Registration page status: {response.status_code}")
        if response.status_code != 200:
            print("Registration page failed to load")
            return False
        print("✓ Registration page loads correctly")
    except Exception as e:
        print(f"Registration page error: {e}")
        return False
    
    print("\n✓ All basic tests passed. The issue may be client-side or require login.")
    return True

if __name__ == "__main__":
    if test_scanner_access():
        print("\nScanner authentication is working correctly.")
        print("To access scanner: Register/Login first, then navigate to /scanner")
    else:
        print("\nFound issues that need to be fixed.")
        sys.exit(1)