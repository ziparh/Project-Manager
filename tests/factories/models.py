from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from modules.users.model import User as UserModel


class UserModelFactory(SQLAlchemyFactory[UserModel]):
    __model__ = UserModel