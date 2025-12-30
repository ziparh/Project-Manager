from fastapi import HTTPException, status

from . import repository, schemas, model, dto
from modules.project_members.model import ProjectMember as ProjectMemberModel
from modules.project_members.repository import ProjectMemberRepository
from common import schemas as common_schemas, dto as common_dto
from core.security.permissions import PermissionChecker
from enums.project_task import ProjectTaskType
from enums.project import ProjectPermission
from utils.datetime import utc_now


class ProjectTaskService:
    def __init__(
        self,
        repo: repository.ProjectTaskRepository,
        member_repo: ProjectMemberRepository,
    ):
        self.repo = repo
        self.member_repo = member_repo

    async def get_all(
        self,
        project_id: int,
        filters: schemas.ProjectTasksFiltersParams,
        sorting: schemas.ProjectTasksSortingParams,
        pagination: common_schemas.BasePaginationParams,
    ) -> common_schemas.BasePaginationResponse[schemas.ProjectTaskRead]:
        filters_dto = dto.ProjectTaskFilterDto(**filters.model_dump(exclude_unset=True))
        sorting_dto = common_dto.SortingDto(**sorting.model_dump(exclude_unset=True))
        pagination_dto = common_dto.PaginationDto(
            size=pagination.size, offset=pagination.offset
        )

        items, total = await self.repo.get_all(
            project_id=project_id,
            filters=filters_dto,
            sorting=sorting_dto,
            pagination=pagination_dto,
        )

        return common_schemas.BasePaginationResponse(
            items=items,
            pagination=common_schemas.BasePaginationMeta(
                total=total,
                page=pagination.page,
                size=pagination.size,
            ),
        )

    async def create(
        self,
        project_id: int,
        actor: ProjectMemberModel,
        task_data: schemas.ProjectTaskCreate,
    ) -> model.ProjectTask:
        task_dict = task_data.model_dump(exclude_unset=True)

        if task_data.type == ProjectTaskType.DEFAULT:
            is_user = await self.member_repo.get_by_user_id_and_project_id(
                project_id=project_id, user_id=task_data.assignee_id
            )
            if not is_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )
            task_dict["assigned_at"] = utc_now()

        task = await self.repo.create(
            project_id=project_id, created_by_id=actor.user_id, data=task_dict
        )

        return task

    async def update(
        self,
        project_id: int,
        task: model.ProjectTask,
        actor: ProjectMemberModel,
        update_data: schemas.ProjectTaskPatch,
    ) -> model.ProjectTask:
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update."
            )

        is_own_task = actor.user_id == task.assignee_id
        update_fields = list(update_dict.keys())

        if is_own_task and update_fields == ["status"]:
            PermissionChecker.require_permission(
                role=actor.role, permission=ProjectPermission.UPDATE_OWN_TASK_STATUS
            )
        else:
            PermissionChecker.require_permission(
                role=actor.role, permission=ProjectPermission.UPDATE_TASKS
            )

        if task.type == ProjectTaskType.DEFAULT and "assignee_id" in update_dict:
            is_user = await self.member_repo.get_by_user_id_and_project_id(
                project_id=project_id, user_id=update_dict["assignee_id"]
            )
            if not is_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )

        if task.type == ProjectTaskType.OPEN and "assignee_id" in update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot add assignee to open task.",
            )

        updated_task = await self.repo.update_by_task(task=task, data=update_dict)

        return updated_task

    async def delete(self, task: model.ProjectTask) -> None:
        await self.repo.delete_by_task(task)

    async def assign(
        self, task: model.ProjectTask, actor: ProjectMemberModel
    ) -> model.ProjectTask:
        if task.assignee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task is already assigned.",
            )
        data = {
            "assignee_id": actor.user_id,
            "assigned_at": utc_now(),
        }

        assigned_task = await self.repo.update_by_task(task=task, data=data)

        return assigned_task

    async def unassign(
        self, task: model.ProjectTask, actor: ProjectMemberModel
    ) -> model.ProjectTask:
        if not task.assignee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Task is not assigned."
            )

        is_own_task = actor.user_id == task.assignee_id
        if not is_own_task and not PermissionChecker.has_permission(
            role=actor.role, permission=ProjectPermission.UPDATE_TASKS
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can unassign only your own tasks.",
            )

        data = {
            "assignee_id": None,
            "assigned_at": None,
        }

        unassigned_task = await self.repo.update_by_task(task=task, data=data)

        return unassigned_task
