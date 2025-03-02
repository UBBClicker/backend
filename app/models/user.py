from odmantic import Model, Field


class User(Model):
    username: str = Field(..., description="The user's username")
    password: str = Field(..., description="The user's password")
