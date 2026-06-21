"""
Profile Service - Database Models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    auth_type = Column(String(20), default="local", nullable=False)
    entra_oid = Column(String(255), unique=True, nullable=True)
    role = Column(String(20), default="patient", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    profile = relationship("PatientProfile", back_populates="user", uselist=False)
    allergies = relationship("FoodAllergy", back_populates="user")

class PatientProfile(Base):
    __tablename__ = "patient_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    medical_conditions = Column(JSON, default=list)
    dietary_preferences = Column(JSON, default=list)
    blood_type = Column(String(10), nullable=True)
    emergency_contact = Column(String(255), nullable=True)
    user = relationship("User", back_populates="profile")

class FoodAllergy(Base):
    __tablename__ = "food_allergies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    allergen_name = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False, default="moderate")
    notes = Column(Text, nullable=True)
    user = relationship("User", back_populates="allergies")
