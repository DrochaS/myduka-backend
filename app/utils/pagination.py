"""
Standardized pagination utility.

Wrap any SQLAlchemy query with Paginator to get consistent page/per_page
handling and a predictable JSON shape across every list endpoint.

Usage in a route:

    from app.utils.pagination import Paginator

    @bp.route("/products", methods=["GET"])
    def list_products():
        query = Product.query.filter_by(store_id=store_id).order_by(Product.name)
        paginator = Paginator(query)
        return jsonify(paginator.to_dict(serializer=lambda p: p.to_dict()))
"""

from flask import request, current_app
from werkzeug.exceptions import BadRequest


class Paginator:
    """
    Applies page/per_page pagination to a SQLAlchemy query and produces
    a standardized response payload.

    Args:
        query: A SQLAlchemy Query object (not yet limited/offset).
        page: Optional override for the page number. If not given, read
              from the `page` query-string parameter.
        per_page: Optional override for page size. If not given, read
                  from the `per_page` query-string parameter.
        max_per_page: Optional cap on per_page. Defaults to app config
                      MAX_PER_PAGE (falls back to 100).
    """

    def __init__(self, query, page=None, per_page=None, max_per_page=None):
        self.query = query
        self.max_per_page = max_per_page or current_app.config.get("MAX_PER_PAGE", 100)

        default_page = current_app.config.get("DEFAULT_PAGE", 1)
        default_per_page = current_app.config.get("DEFAULT_PER_PAGE", 20)

        self.page = page if page is not None else self._parse_int("page", default_page)
        self.per_page = (
            per_page if per_page is not None else self._parse_int("per_page", default_per_page)
        )

        self._validate()

        self.pagination = self.query.paginate(
            page=self.page, per_page=self.per_page, error_out=False
        )

    def _parse_int(self, param_name, default):
        raw_value = request.args.get(param_name, default)
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            raise BadRequest(f"'{param_name}' must be an integer.")

    def _validate(self):
        if self.page < 1:
            raise BadRequest("'page' must be greater than or equal to 1.")
        if self.per_page < 1:
            raise BadRequest("'per_page' must be greater than or equal to 1.")
        if self.per_page > self.max_per_page:
            raise BadRequest(f"'per_page' cannot exceed {self.max_per_page}.")

    @property
    def items(self):
        """The list of ORM objects for the current page."""
        return self.pagination.items

    @property
    def total_records(self):
        return self.pagination.total

    @property
    def total_pages(self):
        return self.pagination.pages

    def to_dict(self, serializer=None):
        """
        Build the standardized response payload.

        Args:
            serializer: Optional callable applied to each item
                        (e.g. `lambda obj: obj.to_dict()`). If omitted,
                        raw ORM objects are returned as-is under "data".

        Returns:
            {
                "data": [...],
                "pagination": {
                    "page": int,
                    "per_page": int,
                    "total_records": int,
                    "total_pages": int,
                    "has_next": bool,
                    "has_prev": bool
                }
            }
        """
        data = [serializer(item) for item in self.items] if serializer else self.items

        return {
            "data": data,
            "pagination": {
                "page": self.page,
                "per_page": self.per_page,
                "total_records": self.total_records,
                "total_pages": self.total_pages,
                "has_next": self.pagination.has_next,
                "has_prev": self.pagination.has_prev,
            },
        }


def paginate(query, serializer=None, page=None, per_page=None, max_per_page=None):
    """
    Convenience function for one-liners in routes.

        return jsonify(paginate(Product.query, serializer=lambda p: p.to_dict()))
    """
    paginator = Paginator(query, page=page, per_page=per_page, max_per_page=max_per_page)
    return paginator.to_dict(serializer=serializer)