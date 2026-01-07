#!/usr/bin/env python3
"""
Quick test script për të kontrolluar frontend
"""
import requests
import sys

def test_frontend():
    base_url = "http://localhost:8080"
    
    print("Testing Frontend...")
    print(f"Base URL: {base_url}")
    
    # Test root
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Root (/) - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to frontend. Is it running?")
        print("   Try: docker-compose up -d frontend")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test static files
    try:
        response = requests.get(f"{base_url}/static/css/simple-style.css", timeout=5)
        print(f"✅ CSS - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ CSS Error: {e}")
    
    # Test JS
    try:
        response = requests.get(f"{base_url}/static/js/dashboard-main.js", timeout=5)
        print(f"✅ JS - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ JS Error: {e}")
    
    # Test API
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"✅ API Health - Status: {response.status_code}")
    except Exception as e:
        print(f"⚠️  API Health Error: {e}")
    
    print("\n✅ Frontend test completed!")
    return True

if __name__ == "__main__":
    test_frontend()
