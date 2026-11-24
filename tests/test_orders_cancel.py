"""Tests for Pedido.puede_cancelar() state validation."""

import pytest

from apps.orders.models import Pedido


@pytest.mark.parametrize("estado", ["pendiente_asignacion", "confirmado"])
def test_pedido_puede_cancelar_returns_true_for_cancellable_states(estado):
    pedido = Pedido(estado=estado)
    assert pedido.puede_cancelar() is True


@pytest.mark.parametrize(
    "estado",
    ["en_preparacion", "en_camino", "entregado", "cancelado"],
)
def test_pedido_puede_cancelar_returns_false_for_non_cancellable_states(estado):
    pedido = Pedido(estado=estado)
    assert pedido.puede_cancelar() is False
