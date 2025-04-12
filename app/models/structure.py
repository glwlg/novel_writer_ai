# backend/app/models/structure.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, Enum as SQLAlchemyEnum, \
    UniqueConstraint
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .base import Base
import enum

class SceneStatus(enum.Enum):
    PLANNED = "PLANNED"
    DRAFTED = "DRAFTED"
    REVISING = "REVISING"
    COMPLETED = "COMPLETED"
    GENERATING = "GENERATING"
    GENERATION_FAILED = "GENERATION_FAILED"

#卷
class Volume(Base):
    __tablename__ = "volumes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True) # What happens in this chapter overall
    order = Column(Integer, nullable=False, default=0) # Order within the project
    embedding = Column(Vector(1024), nullable=True) # Embedding of the summary for high-level context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="volumes")
    chapters = relationship("Chapter", back_populates="volume", order_by="Chapter.order", cascade="all, delete-orphan")
    # scenes = relationship("Scene", back_populates="chapter", order_by="Scene.order_in_chapter", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('project_id', 'title', name='_project_volume_title_uc'),)

class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    volume_id = Column(Integer, ForeignKey("volumes.id"), nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True) # What happens in this chapter overall
    content = Column(Text, nullable=True) # 完整小说内容
    order = Column(Integer, nullable=False, default=0) # Order within the volume
    embedding = Column(Vector(1024), nullable=True) # Embedding of the summary for high-level context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="chapters")
    volume = relationship("Volume", back_populates="chapters")
    scenes = relationship("Scene", back_populates="chapter", order_by="Scene.order_in_chapter", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('project_id', 'title', name='_project_chapter_title_uc'),)


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True) # Can be unassigned initially
    title = Column(String, nullable=True) # Optional short title/slug
    goal = Column(Text, nullable=True) # The objective or key event of this scene - Crucial for generation prompt
    summary = Column(Text, nullable=True) # Summary of what *actually* happens (can be generated post-draft)
    generated_content = Column(Text, nullable=True) # The actual prose generated by the LLM
    order_in_chapter = Column(Integer, nullable=False, default=0) # Order within the chapter
    status = Column(SQLAlchemyEnum(SceneStatus), default=SceneStatus.PLANNED, nullable=False)
    goal_embedding = Column(Vector(1024), nullable=True) # Embedding of the scene's goal for finding relevant context
    summary_embedding = Column(Vector(1024), nullable=True) # Embedding of the scene's summary for future context retrieval
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # project = relationship("Project", back_populates="scenes")
    chapter = relationship("Chapter", back_populates="scenes")
    characters = relationship("Character", secondary="scene_character_association", back_populates="scenes")
    setting_elements = relationship("SettingElement", secondary="scene_setting_association", back_populates="scenes") # Locations, key items used etc.