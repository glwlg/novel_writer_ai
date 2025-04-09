# backend/app/schemas/__init__.py

from .chapter import ChapterCreate, ChapterRead, ChapterUpdate, ChapterReadMinimal
from .character import CharacterCreate, CharacterRead, CharacterUpdate
from .project import ProjectCreate, ProjectRead, ProjectUpdate
from .relationship import CharacterRelationshipCreate, CharacterRelationshipRead, CharacterRelationshipUpdate, \
    RelationshipInfoForCharacterRead
from .scene import SceneCreate, SceneRead, SceneUpdate, SceneReadMinimal
from .setting import SettingElementCreate, SettingElementRead, SettingElementUpdate

