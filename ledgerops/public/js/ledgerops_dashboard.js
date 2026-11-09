frappe.pages["ledgerops-dashboard"].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({ parent: wrapper, title: __("LedgerOps Dashboard"), single_column: true });
    const $body = $(page.body);
    $body.html('<div class="ledgerops-dashboard"><div class="text-muted">Loading reconciliation overview…</div></div>');
    frappe.call({
        method: "ledgerops.ledgerops.api.dashboard.get_overview",
        callback(r) {
            if (!r.message) {
                $body.html('<div class="text-muted">Unable to load dashboard. Check your LedgerOps role and permissions.</div>');
                return;
            }
            const d = r.message;
            const cards = [
                ["Open exceptions", d.open_exceptions],
                ["In review", d.in_review],
                ["Resolved", d.resolved],
                ["Evidence items", d.evidence_items]
            ];
            const html = cards.map(([label, value]) =>
                '<div class="col-sm-3"><div class="card"><div class="card-body"><div class="text-muted">' +
                frappe.utils.escape_html(label) + '</div><h2>' + Number(value || 0) + '</h2></div></div></div>'
            ).join("");
            $body.html('<div class="row">' + html + '</div><div class="mt-4"><a href="/app/ledgerops-exception">' +
                __("Open exception queue") + '</a> · <a href="/app/ledgerops-evidence">' +
                __("Evidence register") + '</a></div>');
        }
    });
};
