"""RAO-P3-005: smoke tests dla nowych modeli SQLAlchemy.

Weryfikujemy że:
- modele importują się bez błędu,
- mają poprawne __tablename__,
- mają oczekiwane kolumny i typy,
- są zarejestrowane w Base.metadata (dzięki czemu create_all je utworzy).
"""
import pytest
from sqlalchemy import Date, DateTime, Integer, Numeric, String


# ── Delivery ────────────────────────────────────────────────────────────────

def test_delivery_model_importable():
    from deliveries.models import Delivery
    assert Delivery.__tablename__ == "deliveries"


def test_delivery_has_required_columns():
    from deliveries.models import Delivery
    cols = {c.name for c in Delivery.__table__.columns}
    expected = {
        "id", "contract_id", "position_id", "delivery_type",
        "scheduled_date", "actual_date", "address", "driver", "note",
        "status", "created_at",
    }
    assert expected <= cols, f"Missing: {expected - cols}"


def test_delivery_fk_contract_cascade():
    from deliveries.models import Delivery
    fk = next(iter(Delivery.__table__.c.contract_id.foreign_keys))
    assert fk.target_fullname == "contracts.id"
    assert fk.ondelete == "CASCADE"


def test_delivery_fk_position_set_null():
    from deliveries.models import Delivery
    fk = next(iter(Delivery.__table__.c.position_id.foreign_keys))
    assert fk.target_fullname == "contract_positions.id"
    assert fk.ondelete == "SET NULL"


def test_delivery_contract_id_not_null():
    from deliveries.models import Delivery
    assert Delivery.__table__.c.contract_id.nullable is False
    assert Delivery.__table__.c.position_id.nullable is True


def test_delivery_address_varchar_500():
    from deliveries.models import Delivery
    col = Delivery.__table__.c.address
    assert isinstance(col.type, String)
    assert col.type.length == 500


# ── ContractCost ────────────────────────────────────────────────────────────

def test_contract_cost_model_importable():
    from contract_costs.models import ContractCost
    assert ContractCost.__tablename__ == "contract_costs"


def test_contract_cost_required_columns():
    from contract_costs.models import ContractCost
    cols = {c.name for c in ContractCost.__table__.columns}
    expected = {
        "id", "contract_id", "position_id", "cost_type",
        "amount", "description", "cost_date", "created_at",
    }
    assert expected <= cols


def test_contract_cost_amount_decimal_10_2():
    from contract_costs.models import ContractCost
    col = ContractCost.__table__.c.amount
    assert isinstance(col.type, Numeric)
    assert col.type.precision == 10
    assert col.type.scale == 2
    assert col.nullable is False


def test_contract_cost_cost_type_required():
    from contract_costs.models import ContractCost
    assert ContractCost.__table__.c.cost_type.nullable is False
    assert ContractCost.__table__.c.cost_type.type.length == 100


# ── AuditLog ────────────────────────────────────────────────────────────────

def test_audit_log_importable():
    from audit.models import AuditLog
    assert AuditLog.__tablename__ == "audit_log"


def test_audit_log_has_columns():
    from audit.models import AuditLog
    cols = {c.name for c in AuditLog.__table__.columns}
    expected = {
        "id", "user_id", "action", "entity_type", "entity_id",
        "old_data", "new_data", "ip_address", "created_at",
    }
    assert expected <= cols


def test_audit_log_action_required():
    from audit.models import AuditLog
    assert AuditLog.__table__.c.action.nullable is False
    assert AuditLog.__table__.c.entity_type.nullable is False
    # entity_id i user_id mogą być NULL (np. login bez encji)
    assert AuditLog.__table__.c.entity_id.nullable is True
    assert AuditLog.__table__.c.user_id.nullable is True


def test_audit_log_user_fk_set_null():
    from audit.models import AuditLog
    fk = next(iter(AuditLog.__table__.c.user_id.foreign_keys))
    assert fk.target_fullname == "users.id"
    assert fk.ondelete == "SET NULL"


def test_audit_log_indexes_present():
    from audit.models import AuditLog
    idx_names = {idx.name for idx in AuditLog.__table__.indexes}
    assert "idx_audit_entity" in idx_names
    assert "idx_audit_created" in idx_names


def test_audit_log_ip_varchar_45():
    """45 znaków = pełny IPv6 z mapowaniem IPv4."""
    from audit.models import AuditLog
    assert AuditLog.__table__.c.ip_address.type.length == 45


# ── Registration in Base.metadata ───────────────────────────────────────────

def test_models_registered_in_base_metadata():
    from database import Base
    import deliveries.models  # noqa
    import contract_costs.models  # noqa
    import audit.models  # noqa

    tables = set(Base.metadata.tables.keys())
    assert "deliveries" in tables
    assert "contract_costs" in tables
    assert "audit_log" in tables
