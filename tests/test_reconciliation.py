from datetime import date

from ledgerops.ledgerops.services.reconciliation import (
    Transaction,
    find_duplicate_fingerprints,
    find_exact_matches,
)


def tx(txid, amount=12500, day=date(2026, 10, 31), ref="UTR123", currency="INR", description="Invoice"):
    return Transaction(txid, amount, day, ref, currency, description)


def test_unique_exact_match():
    matches = find_exact_matches([tx("bank-1")], [tx("ledger-1")])
    assert len(matches) == 1
    assert matches[0].bank_transaction_id == "bank-1"
    assert matches[0].ledger_transaction_id == "ledger-1"


def test_date_window_is_enforced():
    bank = tx("bank-1", day=date(2026, 10, 31))
    ledger = tx("ledger-1", day=date(2026, 10, 29))
    assert find_exact_matches([bank], [ledger], date_window_days=1) == []
    assert len(find_exact_matches([bank], [ledger], date_window_days=2)) == 1


def test_ambiguous_duplicate_reference_is_not_auto_matched():
    banks = [tx("bank-1"), tx("bank-2")]
    ledgers = [tx("ledger-1")]
    assert find_exact_matches(banks, ledgers) == []


def test_amount_or_currency_mismatch_is_not_matched():
    assert find_exact_matches([tx("bank-1")], [tx("ledger-1", amount=12501)]) == []
    assert find_exact_matches([tx("bank-1")], [tx("ledger-1", currency="USD")]) == []


def test_duplicate_fingerprints():
    groups = find_duplicate_fingerprints([tx("a"), tx("b"), tx("c", amount=900)])
    assert len(groups) == 1
    assert set(next(iter(groups.values()))) == {"a", "b"}
