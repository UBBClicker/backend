from odmantic import Model, Field


class User(Model):
    nickname: str = Field(..., description="The user's nickname")
    password: str = Field(..., description="The user's password")
