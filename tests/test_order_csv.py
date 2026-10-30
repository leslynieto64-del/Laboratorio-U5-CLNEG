"""Matriz de casos del laboratorio (datos/casos_de_prueba.csv) ejecutada con csv.DictReader.

Los datos son DIDÁCTICOS y ficticios (no son datos de ningún PIA). Se leen de datos/; los archivos no se modifican.
- pedidos_prueba.csv: total y estado inicial de cada pedido.
- clientes_prueba.csv: si el cliente es VIP y su deuda (atributos del cliente).
- casos_de_prueba.csv: resultado esperado de confirmar cada pedido (CP01-CP12).
CP08 no se toma de la columna resultado_esperado: describe el comportamiento ORIGINAL que el ciclo TDD corrige.
Lo prueba tests/test_tdd_confirmar_dos_veces.py. CP13-CP15 (pago y persistencia) están en test_service.py y test_repository.py.
"""
import csv
from pathlib import Path

import pytest

from src.domain import CustomerHasDebt, Order

DATOS = Path(__file__).resolve().parents[1] / "datos"
CASO_TDD = "CP08"
EXCEPCIONES = {"CustomerHasDebt": CustomerHasDebt, "ValueError": ValueError}


def leer(nombre):
    with (DATOS / nombre).open(encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


PEDIDOS = {fila["pedido_id"]: fila for fila in leer("pedidos_prueba.csv")}
CLIENTES = {fila["cliente_id"]: fila for fila in leer("clientes_prueba.csv")}
CASOS = leer("casos_de_prueba.csv")


def casos_de_confirmacion(exitosos):
    seleccion = []
    for caso in CASOS:
        if caso["accion"] != "confirmar" or caso["caso_id"] == CASO_TDD:
            continue
        if caso["resultado_esperado"].startswith("CONFIRMED") is exitosos:
            pedido = PEDIDOS[caso["pedido_id"]]
            seleccion.append(
                pytest.param(caso, pedido, id=f'{caso["caso_id"]}-{pedido["escenario"]}')
            )
    return seleccion


def pedido_y_deuda(pedido):
    cliente = CLIENTES[pedido["cliente_id"]]
    order = Order(
        float(pedido["total"]), vip=cliente["es_vip"] == "1", status=pedido["estado_inicial"]
    )
    return order, float(cliente["deuda"])


def test_los_datos_didacticos_estan_completos_y_son_coherentes():
    assert len(PEDIDOS) == 12
    assert [c["caso_id"] for c in CASOS] == [f"CP{n:02d}" for n in range(1, 16)]
    for pedido in PEDIDOS.values():
        cliente = CLIENTES[pedido["cliente_id"]]
        assert pedido["es_vip"] == cliente["es_vip"], pedido["pedido_id"]
        assert float(pedido["deuda_cliente"]) == float(cliente["deuda"]), pedido["pedido_id"]


@pytest.mark.parametrize("caso, pedido", casos_de_confirmacion(exitosos=True))
def test_casos_csv_que_se_confirman(caso, pedido):
    # Arrange
    order, deuda = pedido_y_deuda(pedido)
    cobro_esperado = float(caso["resultado_esperado"].split("cobro")[1])
    # Act
    cobro = order.confirm(customer_debt=deuda)
    # Assert
    assert cobro == pytest.approx(cobro_esperado)
    assert order.status == "CONFIRMED"


@pytest.mark.parametrize("caso, pedido", casos_de_confirmacion(exitosos=False))
def test_casos_csv_que_se_rechazan(caso, pedido):
    # Arrange
    order, deuda = pedido_y_deuda(pedido)
    # Act / Assert
    with pytest.raises(EXCEPCIONES[caso["resultado_esperado"]]):
        order.confirm(customer_debt=deuda)
    assert order.status == pedido["estado_inicial"]
    assert order.discount == 0.0
