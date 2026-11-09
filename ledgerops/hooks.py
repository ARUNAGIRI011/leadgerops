app_name = "ledgerops"
app_title = "LedgerOps"
app_publisher = "LedgerOps contributors"
app_description = "Reconciliation exceptions, client evidence and review workflows"
app_email = "maintainers@example.invalid"
app_license = "MIT"
app_version = "0.2.0"

after_install = "ledgerops.ledgerops.services.setup.after_install"
after_migrate = "ledgerops.ledgerops.services.setup.after_migrate"

doctype_js = {
    "LedgerOps Exception": "public/js/ledgerops_exception.js",
}
page_js = {
    "ledgerops-dashboard": "public/js/ledgerops_dashboard.js",
}
