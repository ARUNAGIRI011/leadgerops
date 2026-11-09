import pytest

from ledgerops.ledgerops.services.csv_import import parse_csv_content


def test_parses_bank_statement_and_credit_debit_signs():
    content = (
        "transaction_date,description,reference,debit,credit,currency\n"
        "2026-10-01,Customer payment,UTR-1,0.00,1250.00,INR\n"
        "2026-10-02,Bank fee,CHG-2,25.00,0.00,INR\n"
    )
    rows = parse_csv_content(content)
    assert rows[0].amount_minor == 125000
    assert rows[1].amount_minor == -2500
    assert rows[0].source_row_number == 2


def test_accepts_amount_column_and_indian_date_format():
    rows = parse_csv_content(
        "date,description,reference,amount,currency\n"
        "02/10/2026,Receipt,REF-1,99.50,INR\n"
    )
    assert rows[0].amount_minor == 9950
    assert rows[0].transaction_date.isoformat() == "2026-10-02"


def test_rejects_invalid_date_with_row_number():
    with pytest.raises(ValueError, match="row 2"):
        parse_csv_content("date,amount\nnot-a-date,10.00\n")


def test_rejects_missing_amount_columns():
    with pytest.raises(ValueError, match="amount"):
        parse_csv_content("date,description\n2026-10-01,No amount\n")


def test_rejects_invalid_currency():
    with pytest.raises(ValueError, match="three-letter"):
        parse_csv_content("date,amount,currency\n2026-10-01,10.00,IN\n")
