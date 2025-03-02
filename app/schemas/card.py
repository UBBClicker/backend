from pydantic import BaseModel, Field


class Card(BaseModel):
    image: str = Field(..., description="The card's image")
    name: str = Field(..., description="The card's name")
    description: str = Field(..., description="The card's description")

    asigned_level: int = Field(..., description="The card's level asigned")


__all__ = [
    'Card'
]
