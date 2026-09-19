from pydantic import BaseModel, ConfigDict


class ChatBase(BaseModel):
    pass


class CreateChat(ChatBase):
    user1_id: int
    user2_id: int


class ChatOut(ChatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user1_id: int
    user2_id: int
