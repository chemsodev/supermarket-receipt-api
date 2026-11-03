import pytest
from fastapi.testclient import TestClient

from supermarket_receipt_api.main import app

client = TestClient(app)


def test_empty_checkout_has_zero_totals():
    response = client.post("/checkout", json={"items": []})

    assert response.status_code == 200
    assert response.json() == {
        "lines": [],
        "subtotal_cents": 0,
        "discount_cents": 0,
        "total_cents": 0,
    }


def test_checkout_applies_each_catalog_promotion():
    response = client.post(
        "/checkout",
        json={
            "items": [
                {"product_id": "toothbrush", "quantity": 3},
                {"product_id": "apples", "quantity": 500},
                {"product_id": "rice", "quantity": 1},
                {"product_id": "milk", "quantity": 2},
            ]
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "lines": [
            {
                "product_id": "toothbrush",
                "name": "Brosse à dents",
                "quantity": 3,
                "unit": "piece",
                "unit_price_cents": 99,
                "subtotal_cents": 297,
                "discount_cents": 99,
                "total_cents": 198,
            },
            {
                "product_id": "apples",
                "name": "Pommes",
                "quantity": 500,
                "unit": "gram",
                "unit_price_cents": 199,
                "subtotal_cents": 100,
                "discount_cents": 20,
                "total_cents": 80,
            },
            {
                "product_id": "rice",
                "name": "Sac de riz",
                "quantity": 1,
                "unit": "piece",
                "unit_price_cents": 249,
                "subtotal_cents": 249,
                "discount_cents": 25,
                "total_cents": 224,
            },
            {
                "product_id": "milk",
                "name": "Brique de lait",
                "quantity": 2,
                "unit": "piece",
                "unit_price_cents": 100,
                "subtotal_cents": 200,
                "discount_cents": 0,
                "total_cents": 200,
            },
        ],
        "subtotal_cents": 846,
        "discount_cents": 144,
        "total_cents": 702,
    }


def test_checkout_aggregates_duplicate_products_in_first_seen_order():
    response = client.post(
        "/checkout",
        json={
            "items": [
                {"product_id": "milk", "quantity": 1},
                {"product_id": "toothbrush", "quantity": 2},
                {"product_id": "milk", "quantity": 2},
                {"product_id": "toothbrush", "quantity": 1},
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert [line["product_id"] for line in data["lines"]] == ["milk", "toothbrush"]
    assert [line["quantity"] for line in data["lines"]] == [3, 3]
    assert data["lines"][1]["discount_cents"] == 99


def test_catalog_is_fixed():
    response = client.get("/catalog")

    assert response.status_code == 200
    assert response.json() == {
        "products": [
            {
                "product_id": "toothbrush",
                "name": "Brosse à dents",
                "unit": "piece",
                "unit_price_cents": 99,
                "promotion": "three_for_two",
                "discount_percent": 0,
            },
            {
                "product_id": "apples",
                "name": "Pommes",
                "unit": "gram",
                "unit_price_cents": 199,
                "promotion": "percentage",
                "discount_percent": 20,
            },
            {
                "product_id": "rice",
                "name": "Sac de riz",
                "unit": "piece",
                "unit_price_cents": 249,
                "promotion": "percentage",
                "discount_percent": 10,
            },
            {
                "product_id": "milk",
                "name": "Brique de lait",
                "unit": "piece",
                "unit_price_cents": 100,
                "promotion": "none",
                "discount_percent": 0,
            },
        ]
    }


@pytest.mark.parametrize(
    ("payload", "detail_type"),
    [
        ({}, list),
        ({"items": [{"product_id": "milk"}]}, list),
        ({"items": [{"product_id": "milk", "quantity": 0}]}, list),
        ({"items": [{"product_id": "milk", "quantity": -1}]}, list),
        ({"items": [{"product_id": "milk", "quantity": True}]}, list),
        ({"items": [{"product_id": "milk", "quantity": 1.5}]}, list),
        ({"items": [{"product_id": "milk", "quantity": "2"}]}, list),
        ({"items": [{"product_id": "unknown", "quantity": 1}]}, str),
        ({"items": [], "unexpected": True}, list),
        (
            {"items": [{"product_id": "milk", "quantity": 1, "extra": True}]},
            list,
        ),
    ],
)
def test_invalid_checkout_payloads_are_rejected(payload, detail_type):
    response = client.post("/checkout", json=payload)

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], detail_type)

