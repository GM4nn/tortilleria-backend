# pydantic
from pydantic import BaseModel


class Pagination(BaseModel):
    total_data: int
    total_pages: int
    current_page: int
    next_page: int
    prev_page: int
    last_page: int
    first_page: int = 1
