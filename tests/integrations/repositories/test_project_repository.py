import pytest
import time_machine
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from modules.projects import repository, model, dto as project_dto
from modules.project_members import model as member_model
from common import dto as common_dto
from enums.project import ProjectStatus, ProjectRole

from tests.factories.models import ProjectModelFactory


@pytest.fixture
async def repo(db_session: AsyncSession) -> repository.ProjectRepository:
    return repository.ProjectRepository(db_session)


@pytest.mark.integration
class TestCreate:
    async def test_with_all_fields_success(
        self, repo, test_user, db_session: AsyncSession
    ):
        fixed_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with time_machine.travel(fixed_dt, tick=False):
            create_data = {
                "title": "Test title",
                "description": "Test description",
                "deadline": fixed_dt,
                "status": ProjectStatus.ACTIVE,
            }
            project = await repo.create(
                user_id=test_user.id,
                data=create_data,
            )

            assert isinstance(project.id, int)
            assert project.creator_id == test_user.id
            assert project.title == create_data["title"]
            assert project.description == create_data["description"]
            assert project.deadline == fixed_dt
            assert project.status == ProjectStatus.ACTIVE

            project_in_db = await db_session.get(model.Project, project.id)

            assert project_in_db.id == project.id
            assert project_in_db.creator_id == test_user.id
            assert project_in_db.title == create_data["title"]
            assert project_in_db.description == create_data["description"]
            assert project_in_db.deadline == fixed_dt
            assert project_in_db.status == ProjectStatus.ACTIVE

    async def test_with_minimal_fields_success(
        self, repo, test_user, db_session: AsyncSession
    ):
        create_data = {"title": "Test title"}

        project = await repo.create(
            user_id=test_user.id,
            data=create_data,
        )

        assert isinstance(project.id, int)
        assert project.creator_id == test_user.id
        assert project.title == create_data["title"]

        project_id_db = await db_session.get(model.Project, project.id)

        assert project_id_db.id == project.id
        assert project_id_db.creator_id == test_user.id
        assert project_id_db.title == create_data["title"]

    async def test_creator_in_project_members(
        self, repo, test_user, db_session: AsyncSession
    ):
        create_data = {"title": "Test title"}

        project = await repo.create(
            user_id=test_user.id,
            data=create_data,
        )
        stmt = select(member_model.ProjectMember).where(
            member_model.ProjectMember.user_id == test_user.id,
            member_model.ProjectMember.project_id == project.id,
        )
        result = await db_session.execute(stmt)
        project_member = result.scalar_one_or_none()

        assert project_member is not None
        assert project_member.user_id == test_user.id
        assert project_member.project_id == project.id
        assert project_member.role == ProjectRole.OWNER


@pytest.mark.integration
class TestGetAll:
    async def test_only_where_user_in_project(
        self,
        repo,
        test_user,
        test_multiple_projects,
        other_multiple_projects,
        db_session: AsyncSession,
    ):
        db_session.add(
            member_model.ProjectMember(
                project_id=other_multiple_projects[0].id,
                user_id=test_user.id,
                role=ProjectRole.MEMBER,
            )
        )
        await db_session.commit()

        filters = project_dto.ProjectFilterDto()
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )
        p_ids = [p.id for p in test_multiple_projects]
        p_ids.append(other_multiple_projects[0].id)

        assert total == 4
        assert len(items) == 4

        for item in items:
            assert item.id in p_ids

    async def test_with_creator_id_filter(
        self,
        repo,
        test_user,
        other_user,
        test_multiple_projects,
        other_multiple_projects,
        db_session: AsyncSession,
    ):
        db_session.add(
            member_model.ProjectMember(
                project_id=other_multiple_projects[0].id,
                user_id=test_user.id,
                role=ProjectRole.MEMBER,
            )
        )
        db_session.add(
            member_model.ProjectMember(
                project_id=other_multiple_projects[1].id,
                user_id=test_user.id,
                role=ProjectRole.ADMIN,
            )
        )
        await db_session.commit()

        filters = project_dto.ProjectFilterDto(creator_id=other_user.id)
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )  # Returns projects where the creator is other_user and test_user is a member
        p_ids = [
            other_multiple_projects[0].id,
            other_multiple_projects[1].id,
        ]

        assert total == 2
        for item in items:
            assert item.id in p_ids

    async def test_with_status_filter(self, repo, db_session: AsyncSession, test_user):
        # Project with active status
        active_project = await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id, status=ProjectStatus.ACTIVE
        )
        # Project with completed status
        await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id, status=ProjectStatus.COMPLETED
        )

        filters = project_dto.ProjectFilterDto(status=ProjectStatus.ACTIVE)
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 1
        assert items[0].status == active_project.status

    async def test_with_role_filter(
        self, repo, db_session: AsyncSession, test_user, other_multiple_projects
    ):
        db_session.add(
            member_model.ProjectMember(
                project_id=other_multiple_projects[0].id,
                user_id=test_user.id,
                role=ProjectRole.ADMIN,
            )
        )
        db_session.add(
            member_model.ProjectMember(
                project_id=other_multiple_projects[1].id,
                user_id=test_user.id,
                role=ProjectRole.ADMIN,
            )
        )
        db_session.add(
            member_model.ProjectMember(
                project_id=other_multiple_projects[2].id,
                user_id=test_user.id,
                role=ProjectRole.MEMBER,
            )
        )
        await db_session.commit()

        filters = project_dto.ProjectFilterDto(role=ProjectRole.ADMIN)
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )
        p_ids = [
            other_multiple_projects[0].id,
            other_multiple_projects[1].id,
        ]

        assert total == 2
        for item in items:
            assert item.id in p_ids

    @pytest.mark.parametrize(
        "overdue, expected_indexes",
        [
            (True, [0]),
            (False, [1, 2]),
        ],
    )
    async def test_with_overdue_filter(
        self, repo, db_session: AsyncSession, test_user, overdue, expected_indexes
    ):
        now = datetime.now(timezone.utc)
        projects = [
            # Overdue
            await ProjectModelFactory.create(
                session=db_session,
                creator_id=test_user.id,
                deadline=now - timedelta(days=1),
                status=ProjectStatus.ACTIVE,
            ),
            # Not overdue
            await ProjectModelFactory.create(
                session=db_session,
                creator_id=test_user.id,
                deadline=now + timedelta(days=1),
                status=ProjectStatus.ACTIVE,
            ),
            # Completed(cant be overdue)
            await ProjectModelFactory.create(
                session=db_session,
                creator_id=test_user.id,
                status=ProjectStatus.COMPLETED,
            ),
        ]

        filters = project_dto.ProjectFilterDto(overdue=overdue)
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )
        expected_ids = [projects[i].id for i in expected_indexes]

        assert total == len(expected_indexes)
        for item in items:
            assert item.id in expected_ids

    async def test_with_search_filter_by_title_and_description(
        self, repo, db_session: AsyncSession, test_user
    ):
        game_project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            title="Game",
            description="Racing game",
        )
        models_project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            title="Models",
            description="Models for game",
        )
        todo_list_project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            title="Todo list",
            description="Tasks management",
        )

        filters1 = project_dto.ProjectFilterDto(search="game")
        filters2 = project_dto.ProjectFilterDto(search="tasks")
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items1, total1 = await repo.get_all(
            user_id=test_user.id,
            filters=filters1,
            sorting=sorting,
            pagination=pagination,
        )

        items2, total2 = await repo.get_all(
            user_id=test_user.id,
            filters=filters2,
            sorting=sorting,
            pagination=pagination,
        )
        project_with_game_ids = [game_project.id, models_project.id]
        assert total1 == 2
        for item in items1:
            assert item.id in project_with_game_ids

        assert total2 == 1
        assert items2[0].id == todo_list_project.id

    async def test_with_search_filter_by_creator_name(
        self,
        repo,
        db_session: AsyncSession,
        test_user,
        other_user,
        test_multiple_projects,
        other_multiple_projects,
    ):
        db_session.add(
            member_model.ProjectMember(
                project_id=other_multiple_projects[0].id,
                user_id=test_user.id,
                role=ProjectRole.MEMBER,
            )
        )
        db_session.add(
            member_model.ProjectMember(
                project_id=other_multiple_projects[1].id,
                user_id=test_user.id,
                role=ProjectRole.ADMIN,
            )
        )
        await db_session.commit()

        filters = project_dto.ProjectFilterDto(search=other_user.username)
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )  # Returns projects where the creator name is other_user name and test_user is a member
        expected_ids = [other_multiple_projects[0].id, other_multiple_projects[1].id]

        assert total == 2
        for item in items:
            assert item.id in expected_ids

    async def test_with_multiple_filters(self, repo, db_session, test_user, other_user):
        # Target project
        target_project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            status=ProjectStatus.ON_HOLD,
            members=[
                member_model.ProjectMember(
                    user_id=test_user.id, role=ProjectRole.MEMBER
                )
            ],
        )
        # Non-matching creator_id
        await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id, status=ProjectStatus.ON_HOLD
        )
        # Non-matching status
        await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            status=ProjectStatus.ACTIVE,
            members=[
                member_model.ProjectMember(
                    user_id=test_user.id, role=ProjectRole.MEMBER
                )
            ],
        )
        # Non-matching role
        await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            status=ProjectStatus.ON_HOLD,
            members=[
                member_model.ProjectMember(user_id=test_user.id, role=ProjectRole.ADMIN)
            ],
        )

        filters = project_dto.ProjectFilterDto(
            creator_id=other_user.id,
            status=ProjectStatus.ON_HOLD,
            role=ProjectRole.MEMBER,
        )
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 1
        assert items[0].id == target_project.id

    async def test_with_sorting_asc(self, repo, db_session: AsyncSession, test_user):
        now = datetime.now(timezone.utc)
        p1 = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            deadline=now + timedelta(days=1),
        )
        p2 = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            deadline=now + timedelta(days=2),
        )
        p3 = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            deadline=now + timedelta(days=3),
        )

        filters = project_dto.ProjectFilterDto()
        sorting = common_dto.SortingDto(sort_by="deadline", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 3
        assert items[0].id == p1.id
        assert items[1].id == p2.id
        assert items[2].id == p3.id

    async def test_with_sorting_by_status_desc(
        self, repo, db_session: AsyncSession, test_user
    ):
        p1 = await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id, status=ProjectStatus.PLANNING
        )
        p2 = await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id, status=ProjectStatus.ON_HOLD
        )
        p3 = await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id, status=ProjectStatus.ACTIVE
        )
        p4 = await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id, status=ProjectStatus.COMPLETED
        )
        p5 = await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id, status=ProjectStatus.CANCELLED
        )

        filters = project_dto.ProjectFilterDto()
        sorting = common_dto.SortingDto(sort_by="status", order="desc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 5
        assert items[0].id == p5.id
        assert items[1].id == p4.id
        assert items[2].id == p3.id
        assert items[3].id == p2.id
        assert items[4].id == p1.id

    async def test_with_pagination(self, repo, db_session: AsyncSession, test_user):
        for _ in range(5):
            await ProjectModelFactory.create(
                session=db_session, creator_id=test_user.id
            )

        filters = project_dto.ProjectFilterDto()
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=2, offset=2)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 5
        assert len(items) == 2

    async def test_not_found(self, repo, test_user):
        filters = project_dto.ProjectFilterDto()
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=2, offset=2)

        items, total = await repo.get_all(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 0
        assert len(items) == 0


@pytest.mark.integration
class TestGetById:
    async def test_found(self, repo, test_project):
        project = await repo.get_by_id(test_project.id)

        assert project is not None
        assert project.id == test_project.id
        assert project.creator_id == test_project.creator_id
        assert project.title == test_project.title

    async def test_not_found(self, repo):
        project = await repo.get_by_id(9999)

        assert project is None


@pytest.mark.integration
class TestUpdateById:
    async def test_all_fields_success(
        self, repo, db_session: AsyncSession, test_project
    ):
        deadline = datetime.now(timezone.utc) + timedelta(days=1)
        update_data = {
            "title": "New Title",
            "description": "New Description",
            "deadline": deadline,
            "status": ProjectStatus.CANCELLED,
        }
        updated_project = await repo.update_by_id(
            project_id=test_project.id, data=update_data
        )

        assert updated_project.id == test_project.id
        assert updated_project.title == update_data["title"]
        assert updated_project.description == update_data["description"]
        assert updated_project.deadline == update_data["deadline"]
        assert updated_project.status == update_data["status"]

    async def test_minimal_fields_success(
        self, repo, db_session: AsyncSession, test_project
    ):
        update_data = {"title": "New Title"}

        updated_project = await repo.update_by_id(
            project_id=test_project.id, data=update_data
        )

        assert updated_project.id == test_project.id
        assert updated_project.title == update_data["title"]
        assert updated_project.description == test_project.description
        assert updated_project.deadline == test_project.deadline
        assert updated_project.status == test_project.status

    async def test_not_found(self, repo):
        update_data = {"title": "New Title"}

        updated_project = await repo.update_by_id(project_id=9999, data=update_data)

        assert updated_project is None


@pytest.mark.integration
class TestDeleteById:
    async def test_success(
        self, repo, db_session: AsyncSession, test_user, test_project
    ):
        await repo.delete_by_id(test_project.id)

        project = await db_session.get(model.Project, test_project.id)

        assert project is None

        stmt = select(member_model.ProjectMember).where(
            member_model.ProjectMember.user_id == test_user.id,
            member_model.ProjectMember.project_id == test_project.id,
        )
        result = await db_session.execute(stmt)
        project_member = result.scalar_one_or_none()

        assert project_member is None
