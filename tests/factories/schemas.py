from polyfactory.factories.pydantic_factory import ModelFactory

from modules.auth.schemas import UserRegister


class UserRegisterFactory(ModelFactory[UserRegister]):
    __model__ = UserRegister