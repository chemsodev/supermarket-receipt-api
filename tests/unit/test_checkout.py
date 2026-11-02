"""Tests unitaires de départ pour les calculs de sous-total et de réduction."""

import pytest

from supermarket_receipt_api.checkout import (
    line_subtotal_cents,
    percentage_discount_cents,
    three_for_two_discount_cents,
    validate_quantity,
)


@pytest.mark.parametrize(
    "unit_price_cents, quantity, unit, expected",
    [
        (100, 2, "piece", 200),
        (199, 1000, "gram", 199),
        (199, 2000, "gram", 398),
        (199, 500, "gram", 100),
        (199, 449, "gram", 89),
    ],
)
def test_line_subtotal_nominal(
    unit_price_cents: int, quantity: int, unit: str, expected: int
) -> None:
    """Vérifier des calculs de sous-total.

    Aucun effet de bord ni application HTTP.

    Args:
        unit_price_cents (int): Prix unitaire en centimes fourni par pytest.
        quantity (int): Quantité de pièces ou de grammes fournie par pytest.
        unit (str): Unité de vente du cas paramétré.
        expected (int): Montant brut attendu en centimes.

    Returns:
        None: Le test réussit si le montant calculé correspond à l'attendu.

    Raises:
        AssertionError: Si le montant calculé diffère de expected.
    """
    assert line_subtotal_cents(unit_price_cents, quantity, unit) == expected


@pytest.mark.parametrize(
    "subtotal_cents, discount_percent, expected",
    [(1000, 20, 200), (1200, 10, 120), (800, 25, 200)]
    + [(100 * amount_euros, 10, 10 * amount_euros) for amount_euros in range(20, 114)],
)
def test_percentage_discount_nominal(
    subtotal_cents: int, discount_percent: int, expected: int
) -> None:
    """Vérifier des calculs de réduction en pourcentage.

    Aucun effet de bord ni application HTTP.

    Args:
        subtotal_cents (int): Montant brut en centimes fourni par pytest.
        discount_percent (int): Pourcentage de réduction fourni par pytest.
        expected (int): Réduction attendue en centimes.

    Returns:
        None: Le test réussit si la réduction calculée correspond à l'attendu.

    Raises:
        AssertionError: Si la réduction calculée diffère de expected.
    """
    assert percentage_discount_cents(subtotal_cents, discount_percent) == expected


def test_validate_quantity():
    """Vérifier la validation de la quantité.

    Aucun effet de bord ni application HTTP.

    Returns:
        None: Le test réussit si la quantité est valide.

    Raises:
        AssertionError: Si la quantité est invalide.
    """
    assert validate_quantity(1) == 1
    with pytest.raises(ValueError):
        validate_quantity(-1)
    with pytest.raises(ValueError):
        validate_quantity(0)
    with pytest.raises(TypeError):
        validate_quantity("abc")
    with pytest.raises(TypeError):
        validate_quantity(1.5)
    with pytest.raises(TypeError):
        validate_quantity("1")
    with pytest.raises(TypeError):
        validate_quantity(True)


def test_three_for_two_discount_nominal():
    """Vérifier le calcul de la réduction "3 pour 2".

    Aucun effet de bord ni application HTTP.

    Returns:
        None: Le test réussit si la réduction calculée correspond à l'attendu.

    Raises:
        AssertionError: Si la réduction calculée diffère de expected.
    """
    assert three_for_two_discount_cents(100, 3) == 100
    assert three_for_two_discount_cents(100, 4) == 100
    assert three_for_two_discount_cents(100, 5) == 100
    assert three_for_two_discount_cents(100, 6) == 200
    assert three_for_two_discount_cents(100, 7) == 200
    assert three_for_two_discount_cents(100, 8) == 200
    assert three_for_two_discount_cents(100, 9) == 300
    assert three_for_two_discount_cents(100, 1) == 0
    assert three_for_two_discount_cents(100, 2) == 0
