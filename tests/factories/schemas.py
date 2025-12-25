from polyfactory.factories.pydantic_factory import ModelFactory

from modules.auth.schemas import UserRegister
from modules.projects.schemas import ProjectCreate, ProjectPatch
from modules.project_members.schemas import ProjectMemberAdd, ProjectMemberPatch


class UserRegisterFactory(ModelFactory[UserRegister]):
    __model__ = UserRegister


class ProjectCreateFactory(ModelFactory[ProjectCreate]):
    __model__ = ProjectCreate


class ProjectPatchFactory(ModelFactory[ProjectPatch]):
    __model__ = ProjectPatch


class ProjectMemberAddFactory(ModelFactory[ProjectMemberAdd]):
    __model__ = ProjectMemberAdd


class ProjectMemberPatchFactory(ModelFactory[ProjectMemberPatch]):
    __model__ = ProjectMemberPatch
