from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from modules.users.model import User as UserModel
from modules.personal_tasks.model import PersonalTask as PersonalTaskModel


class UserModelFactory(SQLAlchemyFactory[UserModel]):
    __model__ = UserModel

    __set_relationships__ = False


class PersonalTaskModelFactory(SQLAlchemyFactory[PersonalTaskModel]):
    __model__ = PersonalTaskModel

    __set_relationships__ = False
    __set_foreign_keys__ = False
