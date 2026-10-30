"""Política de cancelación (src/security.py) con fechas FIJAS: el resultado no depende de la hora en que se ejecute.

Reglas implementadas: un pedido SHIPPED nunca se cancela (ni por un administrador); en los demás estados el administrador puede
cancelar; un propietario no administrador solo durante las primeras 24 horas (a las 24 horas exactas ya no).
"""
from datetime import UTC, datetime, timedelta

import pytest

from src.security import can_cancel

AHORA = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
PROPIETARIO, OTRO_USUARIO = 1, 2


def test_owner_within_24h():
    assert can_cancel("NEW", 1, 1, False, AHORA - timedelta(hours=1), AHORA)


def test_stranger_denied():
    assert not can_cancel("NEW", 1, 2, False, AHORA, AHORA)


def test_shipped_denied_even_admin():
    assert not can_cancel("SHIPPED", 1, 1, True, AHORA, AHORA)


def test_expired_denied():
    assert not can_cancel("NEW", 1, 1, False, AHORA - timedelta(hours=25), AHORA)


# Matriz de autorización (evidencia E6): rol, propietario, estado, antigüedad -> permitido/denegado
@pytest.mark.parametrize(
    "estado, usuario, es_admin, antiguedad, permitido",
    [
        ("NEW", PROPIETARIO, False, timedelta(hours=23, minutes=59, seconds=59), True),
        ("NEW", PROPIETARIO, False, timedelta(hours=24), False),
        ("NEW", OTRO_USUARIO, False, timedelta(minutes=5), False),
        ("NEW", OTRO_USUARIO, True, timedelta(minutes=5), True),
        ("NEW", OTRO_USUARIO, True, timedelta(days=30), True),
        ("CONFIRMED", PROPIETARIO, False, timedelta(hours=2), True),
        ("SHIPPED", PROPIETARIO, False, timedelta(hours=1), False),
        ("SHIPPED", OTRO_USUARIO, True, timedelta(hours=1), False),
    ],
    ids=[
        "propietario-a-23h59m59s-permitido",
        "propietario-a-24h-exactas-denegado",
        "tercero-denegado",
        "admin-cancela-pedido-new-de-otro-usuario",
        "admin-sin-limite-de-tiempo",
        "propietario-confirmed-dentro-de-24h",
        "propietario-shipped-denegado",
        "admin-shipped-denegado",
    ],
)
def test_matriz_de_autorizacion(estado, usuario, es_admin, antiguedad, permitido):
    creado = AHORA - antiguedad
    assert can_cancel(estado, PROPIETARIO, usuario, es_admin, creado, now=AHORA) is permitido
