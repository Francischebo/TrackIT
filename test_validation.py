#!/usr/bin/env python3
"""
Basic API validation test for TrackIT backend
"""

import json
import os
import sys

import requests
from flask_jwt_extended import create_access_token

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_app_creation():
    """Test that the Flask app can be created"""
    try:
        from app import create_app

        app = create_app("testing")
        print("[OK] Flask app created successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to create Flask app: {e}")
        return False


def test_blueprint_imports():
    """Test that all blueprints can be imported"""
    try:
        from app.blueprints.assets import assets_bp
        from app.blueprints.audit import audit_bp
        from app.blueprints.auth import auth_bp
        from app.blueprints.departments import departments_bp
        from app.blueprints.inventory import inventory_bp
        from app.blueprints.transfers import transfers_bp

        print("[OK] All blueprints imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import blueprints: {e}")
        return False


def test_models():
    """Test that models can be imported"""
    try:
        from app.models import asset, inventory, organization, user

        print("[OK] All models imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import models: {e}")
        return False


def test_validation():
    """Test that validation schemas can be imported"""
    try:
        from app.validation import AssetSchema, UserRegistrationSchema

        print("[OK] Validation schemas imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import validation schemas: {e}")
        return False


def test_auth_utils():
    """Test that auth utilities can be imported"""
    try:
        from app.auth_utils import jwt_required_with_user, require_role

        print("[OK] Auth utilities imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import auth utilities: {e}")
        return False


def test_transfer_request_lifecycle():
    """Test transfer request lifecycle using the test client"""
    try:
        from datetime import datetime

        from app import create_app, db
        from app.models import asset, organization, user

        app = create_app("testing")
        with app.app_context():
            db.drop_all()
            db.create_all()

            org = organization.Organization(
                name="TestOrg", code="TESTORG", description="Test Org"
            )
            db.session.add(org)
            db.session.commit()

            dept1 = organization.Department(
                name="IT", code="IT", organisation_id=org.id
            )
            dept2 = organization.Department(
                name="HR", code="HR", organisation_id=org.id
            )
            db.session.add_all([dept1, dept2])
            db.session.commit()

            request_user = user.User(
                username="requester",
                email="req@test.com",
                organisation_id=org.id,
                role="staff",
            )
            request_user.set_password("Password123!")
            approver = user.User(
                username="approver",
                email="approve@test.com",
                organisation_id=org.id,
                role="dept_head",
            )
            approver.set_password("Password123!")
            db.session.add_all([request_user, approver])
            db.session.commit()
            dept2.head_id = approver.id
            db.session.commit()

            asset_obj = asset.Asset(
                asset_code="A001",
                name="TestAsset",
                type="Laptop",
                serial_number="SN001",
                department_id=dept1.id,
                assigned_to="User",
                location="Office",
                purchase_date=datetime.utcnow().date(),
                purchase_value=1000.0,
                useful_life=3,
                organisation_id=org.id,
                current_value=1000.0,
                status="active",
            )
            db.session.add(asset_obj)
            db.session.commit()

            token_user = create_access_token(
                identity=str(request_user.id),
                additional_claims={
                    "organisation_id": org.id,
                    "role": request_user.role,
                    "username": request_user.username,
                },
            )
            token_approver = create_access_token(
                identity=str(approver.id),
                additional_claims={
                    "organisation_id": org.id,
                    "role": approver.role,
                    "username": approver.username,
                },
            )

            client = app.test_client()
            response = client.post(
                "/api/transfers/request",
                json={
                    "asset_id": asset_obj.id,
                    "new_department_id": dept2.id,
                    "new_location": "HR Office",
                    "comment": "Need transfer",
                },
                headers={"Authorization": f"Bearer {token_user}"},
            )
            if response.status_code != 201:
                raise RuntimeError(
                    f"Transfer request creation failed: {response.get_json()}"
                )

            request_id = response.get_json().get("request_id")
            if not request_id:
                raise RuntimeError("Transfer request ID missing from response")

            response = client.post(
                f"/api/transfers/requests/{request_id}/approve",
                json={"comments": "Approved"},
                headers={"Authorization": f"Bearer {token_approver}"},
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Transfer request approval failed: {response.get_json()}"
                )

            updated_asset = asset.Asset.query.get(asset_obj.id)
            if updated_asset.department_id != dept2.id:
                raise RuntimeError("Asset department was not updated after approval")

        print("[OK] Transfer request lifecycle passed")
        return True
    except Exception as e:
        print(f"✗ Transfer lifecycle test failed: {e}")
        return False


def test_transfer_request_rejection_and_listing():
    """Test transfer request rejection and request list retrieval"""
    try:
        from datetime import datetime

        from app import create_app, db
        from app.models import asset, organization, transfer, user

        app = create_app("testing")
        with app.app_context():
            db.drop_all()
            db.create_all()

            org = organization.Organization(
                name="TestOrg", code="TESTORG", description="Test Org"
            )
            db.session.add(org)
            db.session.commit()

            dept1 = organization.Department(
                name="IT", code="IT", organisation_id=org.id
            )
            dept2 = organization.Department(
                name="HR", code="HR", organisation_id=org.id
            )
            db.session.add_all([dept1, dept2])
            db.session.commit()

            request_user = user.User(
                username="requester",
                email="req@test.com",
                organisation_id=org.id,
                role="staff",
            )
            request_user.set_password("Password123!")
            approver = user.User(
                username="approver",
                email="approve@test.com",
                organisation_id=org.id,
                role="dept_head",
            )
            approver.set_password("Password123!")
            db.session.add_all([request_user, approver])
            db.session.commit()
            dept2.head_id = approver.id
            db.session.commit()

            asset_obj = asset.Asset(
                asset_code="A001",
                name="TestAsset",
                type="Laptop",
                serial_number="SN001",
                department_id=dept1.id,
                assigned_to="User",
                location="Office",
                purchase_date=datetime.utcnow().date(),
                purchase_value=1000.0,
                useful_life=3,
                organisation_id=org.id,
                current_value=1000.0,
                status="active",
            )
            db.session.add(asset_obj)
            db.session.commit()

            token_user = create_access_token(
                identity=str(request_user.id),
                additional_claims={
                    "organisation_id": org.id,
                    "role": request_user.role,
                    "username": request_user.username,
                },
            )
            token_approver = create_access_token(
                identity=str(approver.id),
                additional_claims={
                    "organisation_id": org.id,
                    "role": approver.role,
                    "username": approver.username,
                },
            )

            client = app.test_client()
            response = client.post(
                "/api/transfers/request",
                json={
                    "asset_id": asset_obj.id,
                    "new_department_id": dept2.id,
                    "new_location": "HR Office",
                    "comment": "Need transfer",
                },
                headers={"Authorization": f"Bearer {token_user}"},
            )
            if response.status_code != 201:
                raise RuntimeError(
                    f"Transfer request creation failed: {response.get_json()}"
                )

            request_id = response.get_json().get("request_id")
            if not request_id:
                raise RuntimeError("Transfer request ID missing from response")

            response = client.post(
                f"/api/transfers/requests/{request_id}/approve",
                json={"comments": "Approved"},
                headers={"Authorization": f"Bearer {token_approver}"},
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Transfer request approval failed: {response.get_json()}"
                )

            updated_asset = asset.Asset.query.get(asset_obj.id)
            if updated_asset.department_id != dept2.id:
                raise RuntimeError("Asset department was not updated after approval")

            response = client.post(
                "/api/transfers/request",
                json={
                    "asset_id": asset_obj.id,
                    "new_department_id": dept1.id,
                    "new_location": "IT Office",
                    "comment": "Return transfer",
                },
                headers={"Authorization": f"Bearer {token_user}"},
            )
            if response.status_code != 201:
                raise RuntimeError(
                    f"Second transfer request creation failed: {response.get_json()}"
                )

            second_request_id = response.get_json().get("request_id")
            if not second_request_id:
                raise RuntimeError("Second transfer request ID missing from response")

            response = client.post(
                f"/api/transfers/requests/{second_request_id}/reject",
                json={"comments": "Not needed"},
                headers={"Authorization": f"Bearer {token_approver}"},
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Transfer request rejection failed: {response.get_json()}"
                )

            rejected_request = transfer.TransferRequest.query.get(second_request_id)
            if rejected_request.status != "rejected":
                raise RuntimeError(
                    "Transfer request status was not updated to rejected"
                )

            current_asset = asset.Asset.query.get(asset_obj.id)
            if current_asset.department_id != dept2.id:
                raise RuntimeError("Asset department changed after rejected request")

            response = client.get(
                "/api/transfers/requests?status=rejected",
                headers={"Authorization": f"Bearer {token_approver}"},
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Request list retrieval failed: {response.get_json()}"
                )

            request_list = response.get_json().get("transfer_requests", [])
            if not any(r["id"] == second_request_id for r in request_list):
                raise RuntimeError(
                    "Rejected transfer request not found in list response"
                )

        print("[OK] Transfer request rejection and listing passed")
        return True
    except Exception as e:
        print(f"✗ Transfer rejection and listing test failed: {e}")
        return False


def test_audit_service():
    """Test that audit service can be imported"""
    try:
        from app.audit_service import AuditService

        print("[OK] Audit service imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import audit service: {e}")
        return False


def test_errors():
    """Test that error classes can be imported"""
    try:
        from app.errors import APIError, NotFoundError, ValidationError

        print("[OK] Error classes imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import error classes: {e}")
        return False


def main():
    """Run all validation tests"""
    print("Running TrackIT Backend Validation Tests")
    print("=" * 50)

    tests = [
        test_app_creation,
        test_blueprint_imports,
        test_models,
        test_validation,
        test_auth_utils,
        test_transfer_request_lifecycle,
        test_transfer_request_rejection_and_listing,
        test_audit_service,
        test_errors,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("All validation tests passed!")
        return 0
    else:
        print("Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
