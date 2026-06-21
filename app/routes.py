"""
Profile Service - API Routes
"""
import logging
import uuid
from typing import Optional, List, Any, Union

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models import User, PatientProfile, FoodAllergy

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["Profile"])

NOT_AUTHENTICATED = "Not authenticated"
INVALID_USER_ID_FORMAT = "Invalid user ID format"


def get_authenticated_user_id(request: Request) -> uuid.UUID:
    user_id_str = request.headers.get("X-User-ID")
    if not user_id_str:
        raise HTTPException(status_code=401, detail=NOT_AUTHENTICATED)
    try:
        return uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=INVALID_USER_ID_FORMAT)


class ProfileUpdateRequest(BaseModel):
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None


class MedicalUpdateRequest(BaseModel):
    medical_conditions: Any = []  # Accepts dict {conditions: [...], other: "..."} or List[str]
    dietary_preferences: List[str] = []


class AllergyCreateRequest(BaseModel):
    allergen_name: str
    severity: str = "moderate"
    notes: Optional[str] = None


@router.get(
    "",
    responses={
        400: {"description": INVALID_USER_ID_FORMAT},
        401: {"description": NOT_AUTHENTICATED},
        404: {"description": "User not found"},
    }
)
async def get_profile(request: Request, db: Session = Depends(get_db)):
    user_id = get_authenticated_user_id(request)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    allergies = db.query(FoodAllergy).filter(FoodAllergy.user_id == user_id).all()

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "age": user.age,
            "gender": user.gender,
            "weight": user.weight,
            "height": user.height,
            "auth_type": user.auth_type,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
        },
        "profile": {
            "medical_conditions": profile.medical_conditions if profile else [],
            "dietary_preferences": profile.dietary_preferences if profile else [],
            "blood_type": profile.blood_type if profile else None,
            "emergency_contact": profile.emergency_contact if profile else None,
        },
        "allergies": [
            {
                "id": str(a.id),
                "allergen_name": a.allergen_name,
                "severity": a.severity,
                "notes": a.notes,
            }
            for a in allergies
        ],
    }


@router.post(
    "/update",
    responses={
        400: {"description": INVALID_USER_ID_FORMAT},
        401: {"description": NOT_AUTHENTICATED},
        404: {"description": "User not found"},
        500: {"description": "Failed to update profile"},
    }
)
async def update_profile(payload: ProfileUpdateRequest, request: Request, db: Session = Depends(get_db)):
    user_id = get_authenticated_user_id(request)

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.full_name = payload.full_name
        if payload.age is not None:
            user.age = payload.age
        if payload.gender:
            user.gender = payload.gender
        if payload.weight is not None:
            user.weight = payload.weight
        if payload.height is not None:
            user.height = payload.height

        profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
        if not profile:
            profile = PatientProfile(user_id=user_id, medical_conditions=[], dietary_preferences=[])
            db.add(profile)

        if payload.blood_type:
            profile.blood_type = payload.blood_type
        if payload.emergency_contact:
            profile.emergency_contact = payload.emergency_contact

        db.commit()
        return {"message": "Profile updated successfully"}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Error updating profile: {e}")
        db.rollback()
        return JSONResponse(status_code=500, content={"error": "Failed to update profile"})


@router.post(
    "/medical",
    responses={
        400: {"description": INVALID_USER_ID_FORMAT},
        401: {"description": NOT_AUTHENTICATED},
        500: {"description": "Failed to update medical info"},
    }
)
async def update_medical(payload: MedicalUpdateRequest, request: Request, db: Session = Depends(get_db)):
    user_id = get_authenticated_user_id(request)

    try:
        # Normalize medical_conditions into {conditions: [...], other: "..."} format
        mc = payload.medical_conditions
        if isinstance(mc, dict):
            conditions = mc.get("conditions", [])
            other_text = mc.get("other", "")
            # Validate: if "None" is selected, it must be the only entry
            if "None" in conditions and len(conditions) > 1:
                return JSONResponse(
                    status_code=400,
                    content={"error": "If 'None' is selected, no other conditions can be chosen."}
                )
            medical_data = {"conditions": conditions, "other": other_text}
        elif isinstance(mc, list):
            # Backward compatibility: convert old array format
            medical_data = {"conditions": mc, "other": ""}
        else:
            medical_data = {"conditions": [], "other": ""}

        profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
        if not profile:
            profile = PatientProfile(user_id=user_id, medical_conditions={}, dietary_preferences=[])
            db.add(profile)

        profile.medical_conditions = medical_data
        profile.dietary_preferences = payload.dietary_preferences
        db.commit()
        return {"message": "Medical information updated successfully"}

    except SQLAlchemyError as e:
        logger.error(f"Error updating medical info: {e}")
        db.rollback()
        return JSONResponse(status_code=500, content={"error": "Failed to update medical info"})


@router.post(
    "/allergy",
    responses={
        400: {"description": INVALID_USER_ID_FORMAT},
        401: {"description": NOT_AUTHENTICATED},
        500: {"description": "Failed to add allergy"},
    }
)
async def add_allergy(payload: AllergyCreateRequest, request: Request, db: Session = Depends(get_db)):
    user_id = get_authenticated_user_id(request)

    try:
        if payload.severity not in ("mild", "moderate", "severe"):
            return JSONResponse(status_code=400, content={"error": "Invalid severity level"})

        allergy = FoodAllergy(
            user_id=user_id,
            allergen_name=payload.allergen_name.strip(),
            severity=payload.severity,
            notes=payload.notes.strip() if payload.notes else None,
        )
        db.add(allergy)
        db.commit()
        db.refresh(allergy)
        return {
            "message": "Allergy added successfully",
            "allergy": {
                "id": str(allergy.id),
                "allergen_name": allergy.allergen_name,
                "severity": allergy.severity,
                "notes": allergy.notes,
            },
        }

    except SQLAlchemyError as e:
        logger.error(f"Error adding allergy: {e}")
        db.rollback()
        return JSONResponse(status_code=500, content={"error": "Failed to add allergy"})


@router.delete(
    "/allergy/{allergy_id}",
    responses={
        400: {"description": INVALID_USER_ID_FORMAT},
        401: {"description": NOT_AUTHENTICATED},
        404: {"description": "Allergy not found"},
        500: {"description": "Failed to remove allergy"},
    }
)
async def delete_allergy(allergy_id: str, request: Request, db: Session = Depends(get_db)):
    user_id = get_authenticated_user_id(request)

    try:
        allergy_uuid = uuid.UUID(allergy_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid allergy ID format"})

    allergy = db.query(FoodAllergy).filter(
        FoodAllergy.id == allergy_uuid,
        FoodAllergy.user_id == user_id,
    ).first()

    if not allergy:
        return JSONResponse(status_code=404, content={"error": "Allergy not found."})

    try:
        db.delete(allergy)
        db.commit()
        return {"message": "Allergy removed successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error deleting allergy: {e}")
        db.rollback()
        return JSONResponse(status_code=500, content={"error": "Failed to remove allergy."})
