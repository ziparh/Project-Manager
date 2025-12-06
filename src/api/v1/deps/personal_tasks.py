from fastapi import Depends

from api.v1.deps.repositories import get_personal_tasks_repository
from modules.personal_tasks import repository as tasks_repo, service as tasks_svc


async def get_personal_tasks_service(
    repo: tasks_repo.PersonalTaskRepository = Depends(get_personal_tasks_repository),
):
    return tasks_svc.PersonalTaskService(repo)
