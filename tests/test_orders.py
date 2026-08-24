from app.orders import OrderLookup


def test_valid_order_lookup():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-1007")

    assert result.found is True
    assert result.order_id == "ORD-1007"
    assert result.status == "shipped"
    assert result.carrier == "UPS"
    assert result.tracking_number == "1ZAR100700000007"


def test_order_id_is_case_insensitive():
    lookup = OrderLookup()

    result = lookup.lookup("ord-1007")

    assert result.found is True
    assert result.order_id == "ORD-1007"


def test_order_id_whitespace_is_normalized():
    lookup = OrderLookup()

    result = lookup.lookup("  ORD-1007  ")

    assert result.found is True
    assert result.order_id == "ORD-1007"


def test_unknown_order_is_safe():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-9999")

    assert result.found is False
    assert result.error == "ORDER_NOT_FOUND"
    assert result.status is None


def test_malformed_order_id_is_rejected():
    lookup = OrderLookup()

    result = lookup.lookup("ABC-123")

    assert result.found is False
    assert result.error == "INVALID_ORDER_ID"


def test_missing_order_id_is_rejected():
    lookup = OrderLookup()

    result = lookup.lookup(None)

    assert result.found is False
    assert result.error == "ORDER_ID_REQUIRED"


def test_cancelled_order_does_not_expose_stale_delivery_data():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-1004")

    assert result.found is True
    assert result.status == "cancelled"
    assert result.carrier is None
    assert result.tracking_number is None
    assert result.estimated_delivery is None


def test_exception_order_does_not_invent_eta():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-1010")

    assert result.found is True
    assert result.status == "exception"
    assert result.estimated_delivery is None


def test_missing_eta_is_preserved_as_missing():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-1011")

    assert result.found is True
    assert result.status == "shipped"
    assert result.carrier == "Canada Post"
    assert result.estimated_delivery is None


def test_customer_safe_result_excludes_internal_fields():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-1007")
    safe_result = lookup.to_customer_safe_dict(result)

    forbidden_fields = {
        "email",
        "customer_email",
        "address",
        "shipping_address",
        "internal_note",
        "warehouse_note",
        "risk_score",
        "support_tags",
    }

    assert forbidden_fields.isdisjoint(
        safe_result.keys()
    )