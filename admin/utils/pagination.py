from fastapi.responses import JSONResponse
from fastapi import Query
from math import ceil
from typing import Any, Optional
from datetime import date

class CustomPagination:
    def __init__(self, page: int, page_size: int):
        self.page = page
        self.page_size = page_size

    def paginate(self, data: Any):
        start = (self.page - 1) * self.page_size
        end = start + self.page_size
        return data[start:end]

    def get_paginated_response(self, data: Any, total: int):
        return JSONResponse({
            'links': {
                'next': f'?page={self.page + 1}&page_size={self.page_size}' if self.page * self.page_size < total else None,
                'previous': f'?page={self.page - 1}&page_size={self.page_size}' if self.page > 1 else None
            },
            'total': total,
            'page_size': self.page_size,
            'pages': ceil(total / self.page_size),
            'data': data
        })

def query_params(page: Optional[int] = Query(None,description="Page number within the paginated result sheet"), limit: Optional[int] = Query(None,description="Number of result to limit per page"), search: Optional[str] = Query(None,description="A search term")):
    return {"page": page, "limit": limit, "search": search}

def start_end_date_params(start_date: date = Query(None,description="Start date 'YYYY-MM-DD"), end_date: date = Query(None,description="End date 'YYYY-MM-DD")):
    return {"start_date": start_date, "end_date": end_date}