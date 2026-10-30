"""Persistencia con SQLAlchemy sobre SQLite EN MEMORIA (la fixture `engine` crea un motor y una base vacía por prueba y los libera al terminar).

No se usa datos/pedidos_prueba.sqlite3 ni ninguna base real: la base didáctica no se modifica.
SQLite en memoria no sustituye las pruebas contra un motor productivo como PostgreSQL.
"""
import csv
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, close_all_sessions

from src.domain import Order
from src.repository import OrderRow, SqlOrderRepository, make_engine

DATOS = Path(__file__).resolve().parents[1] / "datos"


@pytest.fixture
def engine():
    """Motor SQLite en memoria por prueba; cierra sesiones y libera la conexión al terminar."""
    engine = make_engine()
    try:
        yield engine
    finally:
        close_all_sessions()
        engine.dispose()


def contar(engine):
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(OrderRow))


def test_repository_commit(engine):
    with Session(engine) as session:
        SqlOrderRepository(session).save(1, Order(120))
        session.commit()
        assert session.scalar(select(OrderRow).where(OrderRow.id == 1)).total == 120


def test_repository_rollback(engine):
    with Session(engine) as session:
        SqlOrderRepository(session).save(1, Order(120))
        session.rollback()
        assert session.scalar(select(OrderRow).where(OrderRow.id == 1)) is None


# --- Actividad del paso 4 del laboratorio (CP14) ---------------------------------------------------------------------
def test_guardar_y_recuperar_el_pedido_2_con_total_250(engine):
    # Arrange
    # Act
    with Session(engine) as session:
        SqlOrderRepository(session).save(2, Order(250))
        session.commit()
    # Assert: se lee desde una sesión NUEVA, es decir, lo que quedó confirmado en la base
    with Session(engine) as session:
        row = session.get(OrderRow, 2)
        assert (row.id, row.total, row.status) == (2, 250, "NEW")


def test_se_persiste_el_estado_de_un_pedido_confirmado(engine):
    order = Order(200, vip=True)
    order.confirm()
    with Session(engine) as session:
        SqlOrderRepository(session).save(3, order)
        session.commit()
    with Session(engine) as session:
        row = session.get(OrderRow, 3)
        assert (row.total, row.status) == (200, "CONFIRMED")  # se guarda el total, no el importe cobrado


def test_rollback_no_deja_el_registro_visible_para_otra_sesion(engine):  # CP15
    with Session(engine) as session:
        SqlOrderRepository(session).save(4, Order(80))
        session.flush()  # el INSERT ya se envió dentro de la transacción...
        session.rollback()  # ...y se descarta
    assert contar(engine) == 0


# --- Integridad y unicidad -------------------------------------------------------------------------------------------
def test_un_identificador_repetido_viola_la_clave_primaria_y_conserva_el_original(engine):
    with Session(engine) as session:
        SqlOrderRepository(session).save(1, Order(120))
        session.commit()
    with Session(engine) as session:
        SqlOrderRepository(session).save(1, Order(999))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    with Session(engine) as session:
        assert session.get(OrderRow, 1).total == 120
    assert contar(engine) == 1


def test_un_total_nulo_viola_la_restriccion_not_null(engine):
    with Session(engine) as session:
        SqlOrderRepository(session).save(5, Order(None))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    assert contar(engine) == 0


def test_la_transaccion_es_atomica_si_un_registro_falla(engine):
    with Session(engine) as session:
        repo = SqlOrderRepository(session)
        repo.save(10, Order(10))
        repo.save(11, Order(None))  # viola NOT NULL
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    assert contar(engine) == 0  # tampoco se guardó el pedido 10


# --- Datos didácticos ------------------------------------------------------------------------------------------------
def test_los_pedidos_del_csv_se_guardan_en_una_sola_transaccion(engine):
    with (DATOS / "pedidos_prueba.csv").open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    with Session(engine) as session:
        repo = SqlOrderRepository(session)
        for fila in filas:
            repo.save(int(fila["pedido_id"]), Order(float(fila["total"]), status=fila["estado_inicial"]))
        session.commit()
    assert contar(engine) == 12
    with Session(engine) as session:
        assert session.get(OrderRow, 8).status == "CONFIRMED"
        assert session.get(OrderRow, 7).total == pytest.approx(0.01)
