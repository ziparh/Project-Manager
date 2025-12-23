from polyfactory.factories.pydantic_factory import ModelFactory

from modules.auth.schemas import UserRegister
from modules.projects.schemas import ProjectCreate, ProjectPatch


class UserRegisterFactory(ModelFactory[UserRegister]):
    __model__ = UserRegister


class ProjectCreateFactory(ModelFactory[ProjectCreate]):
    __model__ = ProjectCreate


class ProjectPatchFactory(ModelFactory[ProjectPatch]):
    __model__ = ProjectPatch
