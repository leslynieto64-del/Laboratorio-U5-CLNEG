"""TDD (laboratorio U5): un pedido que ya fue confirmado no puede volver a confirmarse (caso CP08 de casos_de_prueba.csv).

Este MISMO archivo está en los dos proyectos:
- TDD_RED_BASELINE (implementación original): las pruebas deben FALLAR con «DID NOT RAISE <class 'ValueError'>», porque
  Order.confirm() permite confirmar dos veces. Es el defecto de negocio que busca la fase RED.
- Proyecto_Laboratorio_U5 (implementación corregida): las pruebas deben PASAR (fases GREEN y REFACTOR).
"""
import pytest

from src.domain import Order


def test_cannot_confirm_twice():
    order = Order(100)
    order.confirm()
    with pytest.raises(ValueError, match="already confirmed"):
        order.confirm()


def test_pedido_cp08_con_estado_inicial_confirmed_no_se_confirma_de_nuevo():
    # Pedido 8 de pedidos_prueba.csv: total 250, cliente regular, estado inicial CONFIRMED.
    order = Order(250, status="CONFIRMED")
    with pytest.raises(ValueError, match="already confirmed"):
        order.confirm()
    assert order.status == "CONFIRMED"
    assert order.discount == 0.0


def test_la_segunda_confirmacion_no_recalcula_el_descuento_vip():
    order = Order(200, vip=True)
    assert order.confirm() == 170
    with pytest.raises(ValueError, match="already confirmed"):
        order.confirm()
    assert order.discount == 30.0
    assert order.status == "CONFIRMED"
