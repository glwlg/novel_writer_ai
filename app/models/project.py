# backend/app/models/project.py
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    logline = Column(Text, nullable=True) # Short pitch/summary
    global_synopsis = Column(Text, nullable=True) # Overall story summary
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    setting_elements = relationship("SettingElement", back_populates="project", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="project", order_by="Chapter.order", cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan") # Direct access to all scenes if needed
    character_relationships = relationship("CharacterRelationship", back_populates="project", cascade="all, delete-orphan")
    # user_id = Column(Integer, ForeignKey("users.id")) # If you add users later
    # user = relationship("User", back_populates="projects")