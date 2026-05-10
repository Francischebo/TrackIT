import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import asset, organization, user
from flask_jwt_extended import create_access_token

def main():
    app = create_app("testing")
    with app.app_context():
        try:
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
            print("Token created")

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
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.get_json()}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
