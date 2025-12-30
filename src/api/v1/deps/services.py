from fastapi import Depends

from api.v1.deps.repositories import (
    get_user_repository,
    get_project_repository,
    get_personal_task_repository,
    get_project_member_repository,
    get_project_task_repository,
)
from modules.auth.service import AuthService
from modules.users.repository import UserRepository
from modules.users.service import UserService
from modules.personal_tasks.repository import PersonalTaskRepository
from modules.personal_tasks.service import PersonalTaskService
from modules.projects.repository import ProjectRepository
from modules.projects.service import ProjectService
from modules.project_members.repository import ProjectMemberRepository
from modules.project_members.service import ProjectMemberService
from modules.project_tasks.repository import ProjectTaskRepository
from modules.project_tasks.service import ProjectTaskService


async def get_auth_service(repo: UserRepository = Depends(get_user_repository)):
    return AuthService(repo)


async def get_user_service(user_repo: UserRepository = Depends(get_user_repository)):
    return UserService(user_repo=user_repo)


async def get_personal_tasks_service(
    repo: PersonalTaskRepository = Depends(get_personal_task_repository),
):
    return PersonalTaskService(repo)


async def get_projects_service(
    repo: ProjectRepository = Depends(get_project_repository),
):
    return ProjectService(repo)


async def get_project_member_service(
    member_repo: ProjectMemberRepository = Depends(get_project_member_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    return ProjectMemberService(member_repo=member_repo, user_repo=user_repo)


async def get_project_tasks_service(
    repo: ProjectTaskRepository = Depends(get_project_task_repository),
    member_repo: ProjectMemberRepository = Depends(get_project_member_repository),
):
    return ProjectTaskService(repo=repo, member_repo=member_repo)
