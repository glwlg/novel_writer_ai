# backend/app/models/setting.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .base import Base

class SettingElement(Base):
    __tablename__ = "setting_elements"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    element_type = Column(String, index=True, nullable=False) # e.g., 'Location', 'Item', 'Concept', 'Lore', 'Rule'
    description = Column(Text, nullable=True)
    embedding = Column(Vector(1024), nullable=True) # Embedding of the description
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="setting_elements")
    scenes = relationship("Scene", secondary="scene_setting_association", back_populates="setting_elements")

    __table_args__ = (UniqueConstraint('project_id', 'name', 'element_type', name='_project_setting_name_type_uc'),)