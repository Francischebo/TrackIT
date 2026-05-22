#!/usr/bin/env python
"""
Minimal app startup test to identify hang points.
Run this to see exactly where the app hangs.
"""
import sys
import os
import time

# Ensure we can import from backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set minimal environment
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('DATABASE_URL', 'sqlite:///trackit_dev.db')
os.environ.setdefault('SECRET_KEY', 'test-dev-key-12345')
os.environ.setdefault('JWT_SECRET_KEY', 'test-dev-jwt-key-12345')
os.environ.setdefault('CORS_ORIGINS', 'http://localhost:3000')

print("[STARTUP TEST] Starting app diagnostic...\n")

# Test 1: Import Flask
print("[1/7] Importing Flask...")
start = time.time()
try:
    from flask import Flask
    print(f"     OK ({time.time() - start:.2f}s)\n")
except Exception as e:
    print(f"     FAILED: {e}\n")
    sys.exit(1)

# Test 2: Import create_app
print("[2/7] Importing create_app function...")
start = time.time()
try:
    os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
    from app import create_app
    print(f"     OK ({time.time() - start:.2f}s)\n")
except Exception as e:
    print(f"     FAILED: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Create app (this is where most hangs happen)
print("[3/7] Creating Flask app instance (this may take a moment)...")
start = time.time()
try:
    app = create_app('development')
    elapsed = time.time() - start
    print(f"     OK ({elapsed:.2f}s)")
    if elapsed > 5:
        print(f"     WARNING: App creation took {elapsed:.2f}s (should be < 2s)\n")
    else:
        print()
except Exception as e:
    print(f"     FAILED: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test app context
print("[4/7] Setting up app context...")
start = time.time()
try:
    with app.app_context():
        pass
    print(f"     OK ({time.time() - start:.2f}s)\n")
except Exception as e:
    print(f"     FAILED: {e}\n")
    sys.exit(1)

# Test 5: Test health endpoint (without database)
print("[5/7] Testing health endpoint...")
start = time.time()
try:
    with app.test_client() as client:
        response = client.get('/health')
        elapsed = time.time() - start
        print(f"     Status: {response.status_code}")
        print(f"     Time: {elapsed:.2f}s")
        if response.status_code == 200:
            print(f"     OK\n")
        else:
            print(f"     WARNING: Expected 200, got {response.status_code}\n")
            print(f"     Response: {response.get_json()}\n")
except Exception as e:
    print(f"     FAILED: {e}\n")
    import traceback
    traceback.print_exc()

# Test 6: Database connection
print("[6/7] Testing database connection...")
start = time.time()
try:
    from sqlalchemy import text
    from app import db
    with app.app_context():
        result = db.session.execute(text("SELECT 1"))
        elapsed = time.time() - start
        print(f"     OK ({elapsed:.2f}s)\n")
except Exception as e:
    print(f"     WARNING: Database connection failed: {e}")
    print(f"     (This may be expected if Supabase is not configured)\n")

# Test 7: List all routes
print("[7/7] App routes registered:")
routes = []
for rule in app.url_map.iter_rules():
    routes.append(rule.rule)
routes = sorted(set(routes))
for route in routes[:20]:  # Show first 20 routes
    print(f"     {route}")
if len(routes) > 20:
    print(f"     ... and {len(routes) - 20} more routes")
print()

print("=" * 60)
print("STARTUP DIAGNOSTIC COMPLETE!")
print("=" * 60)
print("\nIf app hung at step 3, check:")
print("  1. Environment variables: FLASK_ENV, DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY")
print("  2. Supabase status (if using PostgreSQL)")
print("  3. Database connection timeout settings")
print("\nTo start the app normally, run:")
print("  cd backend")
print("  python run.py")
print()
