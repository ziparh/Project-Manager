from fastapi import Depends

from api.v1.deps.repositories import (
    get_user_repository,
    get_project_repository,
    get_personal_task_repository,
    get_project_member_repository,
)
from modules.auth import service as auth_service
from modules.users import repository as user_repository, service as user_service
from modules.personal_tasks import repository as tasks_repo, service as tasks_svc
from modules.projects import repository as project_repo, service as project_svc
from modules.project_members import (
    repository as project_member_repo,
    service as project_member_svc,
)


async def get_auth_service(
    repo: user_repository.UserRepository = Depends(get_user_repository),
):
    return auth_service.AuthService(repo)


async def get_user_service(
    user_repo: user_repository.UserRepository = Depends(get_user_repository),
):
    return user_service.UserService(user_repo=user_repo)


async def get_personal_tasks_service(
    repo: tasks_repo.PersonalTaskRepository = Depends(get_personal_task_repository),
):
    return tasks_svc.PersonalTaskService(repo)


async def get_projects_service(
    repo: project_repo.ProjectRepository = Depends(get_project_repository),
):
    return project_svc.ProjectService(repo)


async def get_project_member_service(
    member_repo: project_member_repo.ProjectMemberRepository = Depends(
        get_project_member_repository
    ),
    user_repo: user_repository.UserRepository = Depends(get_user_repository),
):
    return project_member_svc.ProjectMemberService(
        member_repo=member_repo, user_repo=user_repo
    )
