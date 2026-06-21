import uuid
import pytest
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch

from app.models import User, PatientProfile, FoodAllergy
from app.database import check_db_health

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "profile-service"

def test_check_db_health():
    assert check_db_health() is True
    with patch("app.database.engine.connect", side_effect=SQLAlchemyError("DB error")):
        assert check_db_health() is False

def test_get_profile_unauthenticated(client):
    response = client.get("/profile")
    assert response.status_code == 401

def test_get_profile_not_found(authenticated_client):
    response = authenticated_client.get("/profile")
    assert response.status_code == 404

def test_get_profile_success(authenticated_client, db_session, test_user_id):
    user_uuid = uuid.UUID(test_user_id)
    user = User(
        id=user_uuid,
        email="john@example.com",
        username="john_doe",
        full_name="John Doe",
        auth_type="local"
    )
    profile = PatientProfile(
        user_id=user_uuid,
        medical_conditions={"conditions": ["Hypertension"], "other": ""},
        dietary_preferences=["vegetarian"],
        blood_type="O+",
        emergency_contact="911"
    )
    allergy = FoodAllergy(
        user_id=user_uuid,
        allergen_name="Peanut",
        severity="severe"
    )
    db_session.add(user)
    db_session.add(profile)
    db_session.add(allergy)
    db_session.commit()

    response = authenticated_client.get("/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "john@example.com"
    assert data["profile"]["blood_type"] == "O+"
    assert len(data["allergies"]) == 1
    assert data["allergies"][0]["allergen_name"] == "Peanut"

def test_update_profile_success(authenticated_client, db_session, test_user_id):
    user_uuid = uuid.UUID(test_user_id)
    user = User(
        id=user_uuid,
        email="john@example.com",
        username="john_doe",
        full_name="John Doe",
        auth_type="local"
    )
    db_session.add(user)
    db_session.commit()

    payload = {
        "full_name": "John Doe updated",
        "age": 30,
        "gender": "male",
        "weight": 70.0,
        "height": 180.0,
        "blood_type": "A-",
        "emergency_contact": "112"
    }
    response = authenticated_client.post("/profile/update", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Profile updated successfully"

    # Verify db
    db_session.refresh(user)
    assert user.full_name == "John Doe updated"
    assert user.profile.blood_type == "A-"

def test_update_profile_not_found(authenticated_client):
    payload = {"full_name": "Test User"}
    response = authenticated_client.post("/profile/update", json=payload)
    assert response.status_code == 404

def test_update_profile_db_error(authenticated_client, db_session, test_user_id):
    user_uuid = uuid.UUID(test_user_id)
    user = User(
        id=user_uuid,
        email="john@example.com",
        username="john_doe",
        full_name="John Doe",
        auth_type="local"
    )
    db_session.add(user)
    db_session.commit()

    payload = {"full_name": "New Name"}
    with patch("app.routes.Session.commit", side_effect=SQLAlchemyError("DB update fail")):
        response = authenticated_client.post("/profile/update", json=payload)
        assert response.status_code == 500

def test_update_medical_success(authenticated_client, db_session, test_user_id):
    user_uuid = uuid.UUID(test_user_id)
    user = User(
        id=user_uuid,
        email="john@example.com",
        username="john_doe",
        full_name="John Doe",
        auth_type="local"
    )
    db_session.add(user)
    db_session.commit()

    payload = {
        "medical_conditions": {"conditions": ["Diabetes"], "other": "Gout"},
        "dietary_preferences": ["Keto"]
    }
    response = authenticated_client.post("/profile/medical", json=payload)
    assert response.status_code == 200

    # Test backward compatibility list format
    payload_list = {
        "medical_conditions": ["Diabetes"],
        "dietary_preferences": ["Keto"]
    }
    response = authenticated_client.post("/profile/medical", json=payload_list)
    assert response.status_code == 200

    # Test invalid string format fallback
    payload_invalid = {
        "medical_conditions": "invalid",
        "dietary_preferences": ["Keto"]
    }
    response = authenticated_client.post("/profile/medical", json=payload_invalid)
    assert response.status_code == 200

def test_update_medical_none_validation(authenticated_client):
    payload = {
        "medical_conditions": {"conditions": ["None", "Diabetes"], "other": ""},
        "dietary_preferences": []
    }
    response = authenticated_client.post("/profile/medical", json=payload)
    assert response.status_code == 400
    assert "no other conditions can be chosen" in response.json()["error"]

def test_update_medical_db_error(authenticated_client):
    payload = {
        "medical_conditions": {"conditions": ["Diabetes"], "other": ""},
        "dietary_preferences": []
    }
    with patch("app.routes.Session.commit", side_effect=SQLAlchemyError("DB fail")):
        response = authenticated_client.post("/profile/medical", json=payload)
        assert response.status_code == 500

def test_add_allergy_success(authenticated_client, db_session, test_user_id):
    user_uuid = uuid.UUID(test_user_id)
    user = User(
        id=user_uuid,
        email="john@example.com",
        username="john_doe",
        full_name="John Doe",
        auth_type="local"
    )
    db_session.add(user)
    db_session.commit()

    payload = {
        "allergen_name": "Gluten",
        "severity": "mild",
        "notes": "Stomach pain"
    }
    response = authenticated_client.post("/profile/allergy", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Allergy added successfully"

def test_add_allergy_invalid_severity(authenticated_client):
    payload = {
        "allergen_name": "Gluten",
        "severity": "extreme"
    }
    response = authenticated_client.post("/profile/allergy", json=payload)
    assert response.status_code == 400
    assert "Invalid severity level" in response.json()["error"]

def test_add_allergy_db_error(authenticated_client):
    payload = {
        "allergen_name": "Gluten",
        "severity": "mild"
    }
    with patch("app.routes.Session.commit", side_effect=SQLAlchemyError("DB error")):
        response = authenticated_client.post("/profile/allergy", json=payload)
        assert response.status_code == 500

def test_delete_allergy_success(authenticated_client, db_session, test_user_id):
    user_uuid = uuid.UUID(test_user_id)
    user = User(
        id=user_uuid,
        email="john@example.com",
        username="john_doe",
        full_name="John Doe",
        auth_type="local"
    )
    allergy = FoodAllergy(
        id=uuid.uuid4(),
        user_id=user_uuid,
        allergen_name="Peanut",
        severity="severe"
    )
    db_session.add(user)
    db_session.add(allergy)
    db_session.commit()

    response = authenticated_client.delete(f"/profile/allergy/{allergy.id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Allergy removed successfully."

def test_delete_allergy_not_found(authenticated_client):
    fake_id = uuid.uuid4()
    response = authenticated_client.delete(f"/profile/allergy/{fake_id}")
    assert response.status_code == 404

def test_delete_allergy_db_error(authenticated_client, db_session, test_user_id):
    user_uuid = uuid.UUID(test_user_id)
    user = User(
        id=user_uuid,
        email="john@example.com",
        username="john_doe",
        full_name="John Doe",
        auth_type="local"
    )
    allergy = FoodAllergy(
        id=uuid.uuid4(),
        user_id=user_uuid,
        allergen_name="Peanut",
        severity="severe"
    )
    db_session.add(user)
    db_session.add(allergy)
    db_session.commit()

    with patch("app.routes.Session.commit", side_effect=SQLAlchemyError("DB error")):
        response = authenticated_client.delete(f"/profile/allergy/{allergy.id}")
        assert response.status_code == 500
