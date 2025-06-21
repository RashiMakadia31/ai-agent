from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: Optional[int]
    username: str
    email: str
    password: str
    full_name: Optional[str] = None