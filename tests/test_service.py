"""Servicio de cobro con la pasarela SIMULADA (Mock): ninguna prueba transmite dinero ni llama a un proveedor real (CP13).

Mock(spec_set=["charge"]) solo admite el método charge(): cualquier otra llamada a la pasarela haría fallar la prueba.

Riesgo de consistencia observado (propuesta de mejora, no se oculta): OrderService.checkout() confirma el pedido ANTES de
saber si el cobro fue aceptado; si la pasarela rechaza el pago o falla, el pedido ya quedó CONFIRMED. Propuesta: cobrar sobre el
importe calculado sin cambiar el estado y confirmar solo con el pago aceptado (o revertir el estado si el cobro falla), dentro
de la misma transacción que guarda el pedido.
"""
from unittest.mock import Mock

import pytest

from src.application import OrderService
from src.domain import Order


def pasarela(**configuracion):
    return Mock(spec_set=["charge"], **configuracion)


def test_gateway_approved():
    gateway = Mock()
    gateway.charge.return_value = True
    assert OrderService(gateway).checkout(Order(100)) == 100
    gateway.charge.assert_called_once_with(100)


def test_gateway_rejected():
    gateway = Mock()
    gateway.charge.return_value = False
    with pytest.raises(RuntimeError):
        OrderService(gateway).checkout(Order(100))


def test_pago_aprobado_de_un_pedido_vip_cobra_el_importe_con_descuento():
    # Arrange
    gateway = pasarela(**{"charge.return_value": True})
    # Act
    amount = OrderService(gateway).checkout(Order(200, vip=True))
    # Assert
    assert amount == 170
    gateway.charge.assert_called_once_with(170)


def test_pago_rechazado_de_un_pedido_vip_de_200():  # actividad del paso 5
    gateway = pasarela(**{"charge.return_value": False})
    with pytest.raises(RuntimeError, match="payment rejected"):
        OrderService(gateway).checkout(Order(200, vip=True))
    gateway.charge.assert_called_once_with(170)


@pytest.mark.parametrize(
    "falla",
    [ConnectionError("pasarela no disponible"), TimeoutError("la pasarela no respondio a tiempo")],
    ids=["excepcion-del-servicio", "timeout-simulado"],
)
def test_una_falla_de_la_pasarela_se_propaga_sin_reintentos(falla):
    gateway = pasarela(**{"charge.side_effect": falla})
    with pytest.raises(type(falla)):
        OrderService(gateway).checkout(Order(100))
    assert gateway.charge.call_count == 1  # un solo intento: no hay cobros duplicados
    gateway.charge.assert_called_once_with(100)


@pytest.mark.parametrize("total", [0, -10], ids=["total-cero", "total-negativo"])
def test_si_el_pedido_no_se_puede_confirmar_no_se_intenta_cobrar(total):
    gateway = pasarela(**{"charge.return_value": True})
    order = Order(total)
    with pytest.raises(ValueError):
        OrderService(gateway).checkout(order)
    gateway.charge.assert_not_called()
    assert order.status == "NEW"


def test_un_pedido_ya_confirmado_no_se_cobra_dos_veces():
    gateway = pasarela(**{"charge.return_value": True})
    service = OrderService(gateway)
    order = Order(100)
    assert service.checkout(order) == 100
    with pytest.raises(ValueError, match="already confirmed"):
        service.checkout(order)
    gateway.charge.assert_called_once_with(100)
