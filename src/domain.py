from dataclasses import dataclass

STATUS_NEW = "NEW"
STATUS_CONFIRMED = "CONFIRMED"
VIP_DISCOUNT_RATE = 0.15


class CustomerHasDebt(Exception):
    pass


@dataclass
class Order:
    total: float
    vip: bool = False
    status: str = STATUS_NEW
    discount: float = 0.0

    def confirm(self, customer_debt=0):
        # GREEN (TDD): un pedido ya confirmado no se confirma de nuevo.
        # REFACTOR: validaciones y cálculo del descuento extraídos a métodos privados, sin cambiar el comportamiento.
        self._ensure_can_be_confirmed(customer_debt)
        self.discount = self._vip_discount()
        self.status = STATUS_CONFIRMED
        return self.total - self.discount

    def _ensure_can_be_confirmed(self, customer_debt):
        if self.status == STATUS_CONFIRMED:
            raise ValueError("already confirmed")
        if self.total <= 0:
            raise ValueError("total must be positive")
        if customer_debt > 0:
            raise CustomerHasDebt("outstanding debt")

    def _vip_discount(self):
        return round(self.total * VIP_DISCOUNT_RATE, 2) if self.vip else 0.0
