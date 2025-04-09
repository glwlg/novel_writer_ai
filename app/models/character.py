# backend/app/models/character.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector # Import Vector type
from .base import Base

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True) # Physical appearance, personality traits
    backstory = Column(Text, nullable=True)
    goals = Column(Text, nullable=True) # Motivations, objectives
    arc_summary = Column(Text, nullable=True) # Planned character development
    current_status = Column(Text, nullable=True) # Dynamic field: e.g., "Injured", "In hiding at Location X" - Needs careful management
    embedding = Column(Vector(1024), nullable=True) # Embedding of description, backstory, goals? Needs strategy.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="characters")
    scenes = relationship("Scene", secondary="scene_character_association", back_populates="characters")
    relationships1 = relationship("CharacterRelationship", foreign_keys="[CharacterRelationship.character1_id]", back_populates="character1", cascade="all, delete-orphan")
    relationships2 = relationship("CharacterRelationship", foreign_keys="[CharacterRelationship.character2_id]", back_populates="character2", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('project_id', 'name', name='_project_character_name_uc'),)


class CharacterRelationship(Base):
    __tablename__ = "character_relationships"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False) # Scoping
    character1_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    character2_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    relationship_type = Column(String, nullable=False) # e.g., "Friend", "Enemy", "Family", "Mentor", "Romantic Interest"
    description = Column(Text, nullable=True) # Details about their dynamic
    embedding = Column(Vector(1024), nullable=True) # Embedding of the description
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

     # Relationships
    project = relationship("Project", back_populates="character_relationships")
    character1 = relationship("Character", foreign_keys=[character1_id], back_populates="relationships1")
    character2 = relationship("Character", foreign_keys=[character2_id], back_populates="relationships2")

    __table_args__ = (
        UniqueConstraint('character1_id', 'character2_id', 'relationship_type', name='_character_relationship_uc'),
        # Optional: Check constraint to prevent self-relation if needed
        # CheckConstraint('character1_id != character2_id', name='_check_no_self_relation')
    )