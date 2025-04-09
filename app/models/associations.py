# backend/app/models/associations.py
from sqlalchemy import Table, Column, Integer, ForeignKey, String
from .base import Base

# Association table for Scene <-> Character
scene_character_association = Table(
    "scene_character_association",
    Base.metadata,
    Column("scene_id", Integer, ForeignKey("scenes.id", ondelete="CASCADE"), primary_key=True),
    Column("character_id", Integer, ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True),
    # Optional: Add role if needed, e.g., Point-of-view, Antagonist for the scene
    # Column("role_in_scene", String, nullable=True)
)

# Association table for Scene <-> SettingElement (e.g., locations for the scene)
scene_setting_association = Table(
    "scene_setting_association",
    Base.metadata,
    Column("scene_id", Integer, ForeignKey("scenes.id", ondelete="CASCADE"), primary_key=True),
    Column("setting_element_id", Integer, ForeignKey("setting_elements.id", ondelete="CASCADE"), primary_key=True),
)