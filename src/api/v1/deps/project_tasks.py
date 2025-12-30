from fastapi import Depends, HTTPException, status

from api.v1.deps.repositories import get_project_task_repository
from api.v1.deps.project_members import get_current_project_member
from modules.project_tasks.repository import ProjectTaskRepository
from modules.project_tasks.model import ProjectTask as ProjectTaskModel
from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project_task import ProjectTaskType


async def get_current_project_task(
    task_id: int,
    member: ProjectMemberModel = Depends(get_current_project_member),
    repo: ProjectTaskRepository = Depends(get_project_task_repository),
) -> ProjectTaskModel:
    task = await repo.get_by_id(task_id)

    if not task or task.project_id != member.project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project task not found"
        )

    return task


async def get_current_project_open_task(
    task: ProjectTaskModel = Depends(get_current_project_task),
) -> ProjectTaskModel:
    if task.type != ProjectTaskType.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This operation allowed only for open tasks.",
        )

    return task
