import json
import re
from pathlib import Path

from app.config import DATA_DIR
from app.models import OrderResult


class OrderLookup:
    def __init__(
        self,
        orders_path: Path = DATA_DIR / "orders.json",
    ):
        self.orders_path = Path(orders_path)
        self.orders = self._load_orders()

    def _load_orders(self) -> dict[str, dict]:
        with self.orders_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return {
            order["order_id"]: order
            for order in data["orders"]
        }

    def _normalize_order_id(
        self,
        order_id: str,
    ) -> str:
        return order_id.strip().upper()

    def _is_valid_order_id(
        self,
        order_id: str,
    ) -> bool:
        return bool(
            re.fullmatch(
                r"ORD-\d{4}",
                order_id,
            )
        )

    def lookup(
        self,
        order_id: str | None,
    ) -> OrderResult:
        if not order_id:
            return OrderResult(
                found=False,
                order_id="",
                error="ORDER_ID_REQUIRED",
                message="Please provide your order ID.",
            )

        normalized_id = self._normalize_order_id(
            order_id
        )

        if not self._is_valid_order_id(
            normalized_id
        ):
            return OrderResult(
                found=False,
                order_id=normalized_id,
                error="INVALID_ORDER_ID",
                message="The order ID format is invalid.",
            )

        order = self.orders.get(normalized_id)

        if order is None:
            return OrderResult(
                found=False,
                order_id=normalized_id,
                error="ORDER_NOT_FOUND",
                message="I couldn't find an order with that ID.",
            )

        status = order.get("status")

        carrier = order.get("carrier")
        tracking_number = order.get("tracking_number")
        estimated_delivery = order.get(
            "estimated_delivery"
        )

        if status in {
            "cancelled",
            "returned",
        }:
            carrier = None
            tracking_number = None
            estimated_delivery = None

        if status == "exception":
            estimated_delivery = None

        return OrderResult(
            found=True,
            order_id=normalized_id,
            status=status,
            carrier=carrier,
            tracking_number=tracking_number,
            estimated_delivery=estimated_delivery,
            message=order.get(
                "customer_safe_message"
            ),
        )

    def to_customer_safe_dict(
        self,
        result: OrderResult,
    ) -> dict:
        return {
            "found": result.found,
            "order_id": result.order_id,
            "status": result.status,
            "carrier": result.carrier,
            "tracking_number": result.tracking_number,
            "estimated_delivery": result.estimated_delivery,
            "message": result.message,
            "error": result.error,
        }