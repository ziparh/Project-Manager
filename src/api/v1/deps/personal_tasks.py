from fastapi import Depends, HTTPException, status

from api.v1.deps.auth import get_current_user
from api.v1.deps.repositories import get_personal_task_repository
from modules.personal_tasks.repository import PersonalTaskRepository
from modules.users.model import User as UserModel


async def get_current_personal_task(
    task_id: int,
    user: UserModel = Depends(get_current_user),
    repo: PersonalTaskRepository = Depends(get_personal_task_repository),
):
    task = await repo.get_by_id_and_user(task_id=task_id, user_id=user.id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personal task not found",
        )

    return task
