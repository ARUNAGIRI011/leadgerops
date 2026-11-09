frappe.pages["ledgerops-owner"].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({ parent: wrapper, title: __("LedgerOps Owner Console"), single_column: true });
    const $body = $(page.body);
    const esc = frappe.utils.escape_html;
    $body.html('<div class="text-muted">Loading product and customer metrics…</div>');
    frappe.call({
        method: "ledgerops.ledgerops.api.product_owner.get_overview",
        callback(r) {
            if (!r.message) {
                $body.html('<div class="text-muted">Unable to load owner console. Check Product Owner role.</div>');
                return;
            }
            const d = r.message;
            const cards = [
                ["Total leads", d.leads], ["Open pipeline", d.open_leads],
                ["Customers", d.customers], ["Active customers", d.active_customers],
                ["Subscriptions", d.subscriptions], ["Active subscriptions", d.active_subscriptions],
                ["Open support cases", d.open_support_cases]
            ];
            const cardHtml = cards.map(([label, value]) =>
                '<div class="col-sm-3"><div class="card"><div class="card-body"><div class="text-muted">' +
                esc(label) + '</div><h2>' + Number(value || 0) + '</h2></div></div></div>'
            ).join("");
            const stageRows = (d.leads_by_stage || []).map(x => '<tr><td>' + esc(x.status) + '</td><td>' + Number(x.total) + '</td></tr>').join("");
            const leadRows = (d.recent_leads || []).map(x => '<tr><td><a href="/app/ledgerops-lead/' + encodeURIComponent(x.name) + '">' + esc(x.lead_name) + '</a></td><td>' + esc(x.company || "") + '</td><td>' + esc(x.email) + '</td><td>' + esc(x.status) + '</td></tr>').join("");
            const renewalRows = (d.upcoming_renewals || []).map(x => '<tr><td><a href="/app/ledgerops-subscription/' + encodeURIComponent(x.name) + '">' + esc(x.account) + '</a></td><td>' + esc(x.plan_name) + '</td><td>' + esc(x.status) + '</td><td>' + esc(x.current_period_end || "Not set") + '</td></tr>').join("");
            const moneyRows = (d.mrr_by_currency || []).map(x => '<tr><td>' + esc(x.currency || "") + '</td><td>' + Number(x.amount || 0).toLocaleString() + '</td></tr>').join("");
            const pipelineRows = (d.pipeline_by_currency || []).map(x => '<tr><td>' + esc(x.currency || "") + '</td><td>' + Number(x.amount || 0).toLocaleString() + '</td></tr>').join("");
            $body.html(
                '<div class="row">' + cardHtml + '</div>' +
                '<div class="row mt-4">' +
                '<div class="col-md-6"><div class="card"><div class="card-body"><h4>MRR by currency</h4><table class="table">' + moneyRows + '</table><small class="text-muted">Summed from active and at-risk customer account records; not a recognized-revenue report.</small></div></div></div>' +
                '<div class="col-md-6"><div class="card"><div class="card-body"><h4>Open pipeline by currency</h4><table class="table">' + pipelineRows + '</table><small class="text-muted">Unweighted estimates from open leads, not forecast revenue.</small></div></div></div>' +
                '</div><div class="row mt-4">' +
                '<div class="col-md-4"><div class="card"><div class="card-body"><h4>Lead stages</h4><table class="table">' + stageRows + '</table></div></div></div>' +
                '<div class="col-md-8"><div class="card"><div class="card-body"><h4>Recent leads</h4><table class="table"><thead><tr><th>Name</th><th>Company</th><th>Email</th><th>Status</th></tr></thead><tbody>' + leadRows + '</tbody></table><a href="/app/ledgerops-lead">All leads</a></div></div></div>' +
                '</div><div class="card mt-4"><div class="card-body"><h4>Upcoming subscription periods</h4><table class="table"><thead><tr><th>Customer</th><th>Plan</th><th>Status</th><th>Period ends</th></tr></thead><tbody>' + renewalRows + '</tbody></table><a href="/app/ledgerops-account">Customer accounts</a> · <a href="/app/ledgerops-subscription">Subscriptions</a> · <a href="/app/ledgerops-support-case">Support queue</a></div></div>'
            );
        }
    });
};
