from app.orders import OrderLookup


lookup = OrderLookup()

test_ids = [
    "ORD-1007",
    "ord-1007",
    "  ORD-1007  ",
    "ORD-1004",
    "ORD-1010",
    "ORD-1011",
    "ORD-9999",
    "ABC-123",
    None,
]

for order_id in test_ids:
    result = lookup.lookup(order_id)

    print(
        order_id,
        "->",
        lookup.to_customer_safe_dict(result),
    )