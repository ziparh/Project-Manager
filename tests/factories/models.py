from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users.model import User as UserModel
from modules.personal_tasks.model import PersonalTask as PersonalTaskModel
from modules.projects.model import Project as ProjectModel
from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project import ProjectRole


class UserModelFactory(SQLAlchemyFactory[UserModel]):
    __model__ = UserModel

    __set_relationships__ = False


class PersonalTaskModelFactory(SQLAlchemyFactory[PersonalTaskModel]):
    __model__ = PersonalTaskModel

    __set_relationships__ = False
    __set_foreign_keys__ = False


class ProjectModelFactory(SQLAlchemyFactory[ProjectModel]):
    __model__ = ProjectModel

    __set_relationships__ = False
    __set_foreign_keys__ = False

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        creator_id: int,
        members: list[ProjectMemberModel] | None = None,
        **kwargs,
    ) -> ProjectModel:
        project = cls.build(creator_id=creator_id, **kwargs)

        project.members.append(
            ProjectMemberModel(user_id=creator_id, role=ProjectRole.OWNER)
        )
        if members:
            project.members.extend(members)

        session.add(project)
        await session.commit()

        return project


class ProjectMemberModelFactory(SQLAlchemyFactory[ProjectMemberModel]):
    __model__ = ProjectMemberModel

    __set_relationships__ = False
    __set_foreign_keys__ = False
