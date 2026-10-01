"""
End-to-End Automated Test Suite for Kishore's Platform & SkillSync Logbook
Verifies Flask App, Turso Database CRUD, API Endpoints, and Auth.
"""

import requests
import json
import sys
import time

# Force UTF-8 output formatting for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

def run_tests():
    print("==========================================================")
    print("STARTING E2E AUTOMATED VERIFICATION SUITE")
    print("Target: Kishore's Platform (http://127.0.0.1:5000)")
    print("==========================================================\n")

    session = requests.Session()
    timestamp = int(time.time())
    test_email = f"test_user_{timestamp}@kishore.com"
    test_password = "TestPassword123!"

    passed = 0
    total = 0

    # Helper assertion
    def assert_test(name, success, info=""):
        nonlocal passed, total
        total += 1
        if success:
            passed += 1
            print(f"  [PASS] {name} {f'- {info}' if info else ''}")
        else:
            print(f"  [FAIL] {name} {f'- {info}' if info else ''}")

    # Test 1: Check Home Page & Kishore's Platform branding
    try:
        r = session.get(f"{BASE_URL}/")
        has_branding = ("Kishore's Platform" in r.text) or ("Kishore" in r.text)
        assert_test("1. Landing Page Load & Branding Check", r.status_code == 200 and has_branding, f"Status {r.status_code}")
    except Exception as e:
        assert_test("1. Landing Page Load", False, str(e))
        print("\nCould not connect to server. Is app.py running?")
        sys.exit(1)

    # Test 2: Register New Student User
    payload_register = {
        "name": "Kishore Tester",
        "email": test_email,
        "password": test_password,
        "combo": "AWS+DEVOPS",
        "pin": "21AK1A0501"  # Exactly 10 alphanumeric chars
    }
    r = session.post(f"{BASE_URL}/api/register", json=payload_register)
    data = r.json() if r.headers.get("content-type") == "application/json" else {}
    reg_ok = r.status_code in (200, 201) and ("user" in data or data.get("message") == "Registration successful")
    assert_test("2. User Registration (Turso Cloud DB)", reg_ok, data.get("message", r.text[:100]))

    # Test 3: Login User
    payload_login = {
        "email": test_email,
        "password": test_password
    }
    r = session.post(f"{BASE_URL}/api/login", json=payload_login)
    data = r.json() if r.headers.get("content-type") == "application/json" else {}
    login_ok = r.status_code == 200 and ("user" in data)
    assert_test("3. Student Login Auth", login_ok, data.get("message", r.text[:100]))

    # Test 4: Save Daily Training Log
    payload_log = {
        "user_email": test_email,
        "combo": "AWS+DEVOPS",
        "date": "2026-10-01",
        "day": "Day 45",
        "lab": "Lab 1 - AWS Operations",
        "trainer": "Kishore Kumar",
        "checkIn": "09:00 AM",
        "checkOut": "05:00 PM",
        "topics": "• Topic 1: AWS VPC Container Networking\n• Topic 2: Turso Cloud Database Integration",
        "practical": "• Step 1: Deployed Flask app with HTTP DBAPI wrapper to Turso DB",
        "assignment": "• Task 1: Complete E2E automated test suite execution",
        "doubts": "• None"
    }
    r = session.post(f"{BASE_URL}/api/logs", json=payload_log)
    data = r.json() if r.headers.get("content-type") == "application/json" else {}
    log_ok = r.status_code in (200, 201) and ("log" in data)
    assert_test("4. Save Daily Training Log (Turso Cloud)", log_ok, data.get("message", r.text[:100]))

    # Test 5: Retrieve Daily Logs
    r = session.get(f"{BASE_URL}/api/logs?email={test_email}")
    data = r.json() if isinstance(r.json(), list) else []
    assert_test("5. Retrieve Daily Logs API", r.status_code == 200 and len(data) > 0, f"Retrieved {len(data)} log(s) from Turso DB")

    # Test 6: Submit Suggestion / Feedback
    payload_sug = {
        "name": "Kishore Tester",
        "email": test_email,
        "category": "Feature Request",
        "subject": "Voice AI Feedback",
        "message": "The platform and voice logging work amazingly well!"
    }
    r = session.post(f"{BASE_URL}/api/suggestions", json=payload_sug)
    data = r.json() if r.headers.get("content-type") == "application/json" else {}
    sug_ok = r.status_code in (200, 201) and ("suggestion" in data or data.get("status") == "success")
    assert_test("6. Submit Suggestion API", sug_ok, data.get("message", r.text[:100]))

    # Test 7: Admin Master Overview Endpoint
    r = session.get(f"{BASE_URL}/api/owner/master?passcode=admin123")
    data = r.json() if isinstance(r.json(), dict) else {}
    assert_test("7. Admin Master Overview API", r.status_code == 200 and "users" in data, f"Total Registered Users: {len(data.get('users', []))}")

    # Test 8: AI Voice Parser API
    payload_ai = {
        "text": "topics covered today Docker containerization and AWS VPC deployment",
        "target_section": "topics"
    }
    r = session.post(f"{BASE_URL}/api/ai/parse-voice", json=payload_ai)
    data = r.json() if isinstance(r.json(), dict) else {}
    assert_test("8. AI Voice Parser API", r.status_code == 200 and "topics" in data, f"Parsed: {data.get('target_name', 'OK')}")

    print("\n==========================================================")
    print(f"VERIFICATION RESULTS: {passed} / {total} PASSED ({int(passed/total*100)}%)")
    print("==========================================================\n")

if __name__ == "__main__":
    run_tests()
