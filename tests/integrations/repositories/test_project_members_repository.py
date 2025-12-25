import pytest
import time_machine
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_members import repository, model, dto as member_dto
from modules.projects import model as project_model
from common import dto as common_dto
from enums.project import ProjectRole

from tests.factories.models import ProjectModelFactory, UserModelFactory


@pytest.fixture
async def repo(db_session: AsyncSession) -> repository.ProjectMemberRepository:
    return repository.ProjectMemberRepository(db_session)


@pytest.mark.integration
class TestCreate:
    async def test_success(
        self, repo, db_session: AsyncSession, other_user, test_project
    ):
        fixed_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with time_machine.travel(fixed_dt, tick=False):
            membership = await repo.create(
                project_id=test_project.id,
                user_id=other_user.id,
                role=ProjectRole.MEMBER,
            )

        assert membership
        assert isinstance(membership.id, int)
        assert membership.project_id == test_project.id
        assert membership.user_id == other_user.id
        assert membership.role == ProjectRole.MEMBER
        assert membership.joined_at == fixed_dt

        db_membership = await db_session.get(model.ProjectMember, membership.id)

        assert db_membership
        assert db_membership.project_id == test_project.id
        assert db_membership.user_id == other_user.id
        assert db_membership.role == ProjectRole.MEMBER
        assert db_membership.joined_at == fixed_dt


@pytest.mark.integration
class TestGetAll:
    async def test_only_in_project(
        self, repo, db_session: AsyncSession, test_user, other_user, test_project
    ):
        other_project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            members=[model.ProjectMember(user_id=other_user.id)],
        )

        filters = member_dto.ProjectMemberFilterDto()
        sorting = common_dto.SortingDto(sort_by="joined_at")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=other_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )
        user_ids = [m.user_id for m in other_project.members]

        assert total == 2
        assert len(items) == 2

        for item in items:
            assert item.project_id == other_project.id
            assert item.user_id in user_ids

    async def test_with_role_filter(
        self, repo, db_session: AsyncSession, test_user, other_user
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            members=[
                model.ProjectMember(user_id=other_user.id, role=ProjectRole.ADMIN)
            ],
        )

        filters = member_dto.ProjectMemberFilterDto(role=ProjectRole.OWNER)
        sorting = common_dto.SortingDto(sort_by="joined_at")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0].project_id == project.id
        assert items[0].user_id == test_user.id

    async def test_with_sorting_by_joined_at_asc(
        self, repo, db_session: AsyncSession, test_user, other_user
    ):
        user3 = UserModelFactory.build()
        db_session.add(user3)
        await db_session.commit()

        now = datetime.now(timezone.utc)
        project = project_model.Project(creator_id=test_user.id, title="Test")
        m1 = model.ProjectMember(
            project_id=project.id,
            user_id=test_user.id,
            role=ProjectRole.OWNER,
            joined_at=now - timedelta(days=3),
        )
        m2 = model.ProjectMember(
            project_id=project.id,
            user_id=other_user.id,
            joined_at=now - timedelta(days=2),
        )
        m3 = model.ProjectMember(
            project_id=project.id,
            user_id=user3.id,
            joined_at=now - timedelta(days=1),
        )
        project.members.extend([m1, m2, m3])

        db_session.add(project)
        await db_session.commit()

        filters = member_dto.ProjectMemberFilterDto()
        sorting = common_dto.SortingDto(sort_by="joined_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 3
        assert items[0].id == m1.id
        assert items[1].id == m2.id
        assert items[2].id == m3.id

    async def test_with_sorting_by_role_desc(
        self, repo, db_session: AsyncSession, test_user, other_user
    ):
        user3 = UserModelFactory.build()
        db_session.add(user3)
        await db_session.commit()

        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            members=[
                model.ProjectMember(user_id=other_user.id, role=ProjectRole.ADMIN),
                model.ProjectMember(user_id=user3.id, role=ProjectRole.MEMBER),
            ],
        )

        filters = member_dto.ProjectMemberFilterDto()
        sorting = common_dto.SortingDto(sort_by="role", order="desc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 3
        assert items[0].role == ProjectRole.OWNER
        assert items[1].role == ProjectRole.ADMIN
        assert items[2].role == ProjectRole.MEMBER

    async def test_with_pagination(self, repo, db_session: AsyncSession, test_user):
        users = [UserModelFactory.build() for _ in range(4)]
        members = [model.ProjectMember(user_id=user.id) for user in users]

        db_session.add_all(users)
        await db_session.commit()

        project = await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id, members=members
        )

        filters = member_dto.ProjectMemberFilterDto()
        sorting = common_dto.SortingDto(sort_by="joined_at")
        pagination = common_dto.PaginationDto(size=2, offset=2)

        items, total = await repo.get_all(
            project_id=project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 5
        assert len(items) == 2

    async def test_not_found(self, repo, db_session: AsyncSession, test_user):
        project = project_model.Project(creator_id=test_user.id, title="Test")
        db_session.add(project)
        await db_session.commit()

        filters = member_dto.ProjectMemberFilterDto()
        sorting = common_dto.SortingDto(sort_by="joined_at")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 0
        assert len(items) == 0


@pytest.mark.integration
class TestGetByUserIdAndProjectId:
    async def test_success(self, repo, test_user, test_project):
        result = await repo.get_by_user_id_and_project_id(
            user_id=test_user.id, project_id=test_project.id
        )

        assert result
        assert result.user_id == test_project.id
        assert result.project_id == test_project.id

    async def test_not_found_for_wrong_user_id(self, repo, other_user, test_project):
        result = await repo.get_by_user_id_and_project_id(
            user_id=other_user.id, project_id=test_project.id
        )

        assert not result

    async def test_not_found_for_wrong_project_id(
        self, repo, db_session: AsyncSession, test_user
    ):
        result = await repo.get_by_user_id_and_project_id(
            user_id=test_user.id, project_id=9999
        )

        assert not result


@pytest.mark.integration
class TestUpdateByMembership:
    async def test_success(
        self, repo, db_session: AsyncSession, other_user, test_project
    ):
        membership = model.ProjectMember(
            project_id=test_project.id,
            user_id=other_user.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(membership)
        await db_session.commit()

        await repo.update_by_membership(
            membership=membership, data={"role": ProjectRole.ADMIN}
        )

        await db_session.refresh(membership)

        assert membership.role == ProjectRole.ADMIN


@pytest.mark.integration
class TestDeleteByMembership:
    async def test_success(
        self, repo, db_session: AsyncSession, other_user, test_project
    ):
        membership = model.ProjectMember(
            project_id=test_project.id, user_id=other_user.id
        )
        db_session.add(membership)
        await db_session.commit()

        await repo.delete_by_membership(membership)

        db_membership = await db_session.get(model.ProjectMember, membership.id)

        assert not db_membership
