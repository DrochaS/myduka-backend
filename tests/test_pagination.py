from app.utils.pagination import paginate_query


def test_paginate_query_defaults(app, product):
    with app.test_request_context("/?"):
        result = paginate_query(type(product).query)
        assert result["page"] == 1
        assert result["per_page"] == 20


def test_paginate_query_clamps_per_page(app, product):
    with app.test_request_context("/?per_page=500"):
        result = paginate_query(type(product).query)
        assert result["per_page"] == 100


def test_paginate_query_rejects_zero_page(app, product):
    with app.test_request_context("/?page=0"):
        result = paginate_query(type(product).query)
        assert result["page"] == 1
