import pytest

from src.domain import CustomerHasDebt, Order


def test_vip_discount():
    o = Order(100, vip=True)
    assert o.confirm() == 85
    assert o.status == "CONFIRMED"


def test_regular_no_discount():
    assert Order(100).confirm() == 100


def test_customer_debt():
    with pytest.raises(CustomerHasDebt):
        Order(100).confirm(customer_debt=50)


@pytest.mark.parametrize("total", [0, -1])
def test_invalid_total(total):
    with pytest.raises(ValueError):
        Order(total).confirm()


# --- Actividad del paso 2 del laboratorio ---------------------------------------------------------------------------
def test_vip_200_cobra_170():
    # Arrange
    order = Order(200, vip=True)
    # Act
    amount = order.confirm()
    # Assert
    assert amount == 171
    assert order.discount == 30.0
    assert order.status == "CONFIRMED"


def test_regular_200_cobra_200_sin_descuento():
    order = Order(200)
    assert order.confirm() == 200
    assert order.discount == 0.0
    assert order.status == "CONFIRMED"


def test_descuento_vip_es_el_15_por_ciento():
    order = Order(total=100, vip=True)
    order.confirm()
    assert order.discount == 15


# --- Límites ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "total, vip, cobro",
    [
        (0.01, False, 0.01),  # menor importe positivo
        (0.01, True, 0.01),  # 15 % de 0.01 se redondea a 0.00
        (99.99, True, 84.99),  # 15 % de 99.99 = 14.9985 -> 15.00
    ],
    ids=["centavo-regular", "centavo-vip-sin-descuento", "redondeo-vip-99.99"],
)
def test_importes_pequenos_y_redondeo(total, vip, cobro):
    assert Order(total, vip=vip).confirm() == pytest.approx(cobro)


@pytest.mark.parametrize(
    "deuda, permitido",
    [(0, True), (0.01, False)],
    ids=["sin-deuda-confirma", "un-centavo-de-deuda-rechaza"],
)
def test_limite_de_la_deuda_del_cliente(deuda, permitido):
    order = Order(100)
    if permitido:
        assert order.confirm(customer_debt=deuda) == 100
    else:
        with pytest.raises(CustomerHasDebt):
            order.confirm(customer_debt=deuda)


@pytest.mark.parametrize(
    "order, debt, error",
    [
        (Order(100, vip=True), 50, CustomerHasDebt),
        (Order(0, vip=True), 0, ValueError),
        (Order(-10), 0, ValueError),
    ],
    ids=["deuda", "total-cero", "total-negativo"],
)
def test_una_confirmacion_rechazada_no_modifica_el_pedido(order, debt, error):
    with pytest.raises(error):
        order.confirm(customer_debt=debt)
    assert order.status == "NEW"
    assert order.discount == 0.0


def test_el_importe_invalido_se_valida_antes_que_la_deuda():
    with pytest.raises(ValueError, match="total must be positive"):
        Order(0).confirm(customer_debt=500)
