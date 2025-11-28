from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from polyfactory.factories.pydantic_factory import ModelFactory

from modules.users.model import User as UserModel
from modules.auth.schemas import UserRegister


class DBUserFactory(SQLAlchemyFactory[UserModel]):
    __model__ = UserModel


class RegisterUserFactory(ModelFactory[UserRegister]):
    __model__ = UserRegister
