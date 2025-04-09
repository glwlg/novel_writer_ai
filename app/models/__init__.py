# backend/app/models/__init__.py

from .base import Base
from .project import Project
from .character import Character, CharacterRelationship
from .setting import SettingElement
from .structure import Chapter, Scene
from .associations import scene_character_association, scene_setting_association