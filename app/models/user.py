from odmantic import Model, Field, Index


class User(Model):
    nickname: str = Field(..., description="The user's nickname")
    password: str = Field(..., description="The user's password")

    model_config = {
        "indexes": lambda: [
            Index(User.nickname, unique=True),
        ]
    }
