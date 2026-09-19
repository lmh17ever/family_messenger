from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str


class CreateUser(UserBase):
    password: str


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
