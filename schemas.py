from pydantic import BaseModel


class AppModel(BaseModel):
    pass


class Book(AppModel):
    name: str
    publish: str
    type: str
    author: str
    info: str
    price: int
