"""Simple pagination helpers."""

from flask import request


def paginate_query(query, default_per_page=20, max_per_page=100):
    page = request.args.get("page", 1, type=int) or 1
    per_page = request.args.get("per_page", default_per_page, type=int) or default_per_page
    per_page = min(max(per_page, 1), max_per_page)
    page = max(page, 1)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": pagination.items,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }
