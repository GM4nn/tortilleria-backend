# other libs
from math import ceil

# sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import Session

# app
from app.src.schemas.pagination import Pagination


class PaginationProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def get_pagination_data(self, model, offset: int, limit: int, filters=None) -> Pagination:
        query = self._db_session.query(func.count(model.id))

        if filters:
            query = query.filter(*filters)

        total_data = query.scalar() or 0
        per_page = limit or 1
        total_pages = ceil(total_data / per_page) or 1
        current_page = (offset // per_page) + 1

        return Pagination(
            total_data=total_data,
            total_pages=total_pages,
            current_page=current_page,
            next_page=current_page + 1,
            prev_page=current_page - 1,
            last_page=total_pages,
        )
