frappe.pages["ledgerops-owner"].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({ parent: wrapper, title: __("LedgerOps Owner Console"), single_column: true });
    const $body = $(page.body);
    const esc = frappe.utils.escape_html;

    function renderCustomers(search = "", status = "") {
        const $target = $body.find("#lo-customers-body");
        $target.html('<tr><td colspan="7" class="text-muted">Loading customers…</td></tr>');
        frappe.call({
            method: "ledgerops.ledgerops.api.product_owner.list_customers",
            args: { search, lifecycle_status: status, limit_start: 0, page_length: 50 },
            callback(r) {
                const rows = (r.message || []).map(x =>
                    '<tr><td><a href="/app/ledgerops-account/' + encodeURIComponent(x.name) + '">' + esc(x.account_name) + '</a></td>' +
                    '<td>' + esc(x.primary_email || "") + '</td><td>' + esc(x.country || "") + '</td>' +
                    '<td>' + esc(x.account_type || "") + '</td><td>' + esc(x.lifecycle_status || "") + '</td>' +
                    '<td>' + esc(x.plan || "—") + '</td><td>' + esc(x.currency || "") + ' ' + Number(x.monthly_recurring_revenue || 0).toLocaleString() + '</td></tr>'
                ).join("");
                $target.html(rows || '<tr><td colspan="7" class="text-muted">No customers found.</td></tr>');
            }
        });
    }

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
                '<div class="col-md-4"><div class="card"><div class="card-body"><h4>Lead stages</h4><table class="table">' + stageRows + '</table><a href="/app/ledgerops-lead">Manage leads</a></div></div></div>' +
                '<div class="col-md-8"><div class="card"><div class="card-body"><h4>Recent leads</h4><table class="table"><thead><tr><th>Name</th><th>Company</th><th>Email</th><th>Status</th></tr></thead><tbody>' + leadRows + '</tbody></table></div></div></div>' +
                '</div>' +
                '<div class="card mt-4"><div class="card-body"><div class="d-flex justify-content-between align-items-center flex-wrap"><h4>Customer management</h4><a class="btn btn-primary btn-sm" href="/app/ledgerops-account/new-ledgerops-account-1">Add customer</a></div>' +
                '<div class="row mb-3"><div class="col-md-5"><input id="lo-customer-search" class="form-control" placeholder="Search company, email or country"></div>' +
                '<div class="col-md-3"><select id="lo-customer-status" class="form-control"><option value="">All lifecycle statuses</option><option>Onboarding</option><option>Active</option><option>At Risk</option><option>Suspended</option><option>Churned</option></select></div>' +
                '<div class="col-md-2"><button id="lo-customer-search-btn" class="btn btn-default">Search</button></div></div>' +
                '<div class="table-responsive"><table class="table table-hover"><thead><tr><th>Customer</th><th>Email</th><th>Country</th><th>Type</th><th>Status</th><th>Plan</th><th>MRR</th></tr></thead><tbody id="lo-customers-body"><tr><td colspan="7">Loading…</td></tr></tbody></table></div>' +
                '<small class="text-muted">Showing up to 50 records. Use the full customer list for larger datasets.</small> <a href="/app/ledgerops-account">Open customer register</a></div></div>' +
                '<div class="card mt-4"><div class="card-body"><h4>Upcoming subscription periods</h4><table class="table"><thead><tr><th>Customer</th><th>Plan</th><th>Status</th><th>Period ends</th></tr></thead><tbody>' + renewalRows + '</tbody></table><a href="/app/ledgerops-subscription">Manage subscriptions</a> · <a href="/app/ledgerops-support-case">Support queue</a> · <a href="/app/ledgerops-contact">Contacts</a> · <a href="/app/ledgerops-crm-activity">Activities</a></div></div>'
            );
            renderCustomers();
            $body.find("#lo-customer-search-btn").on("click", () => renderCustomers($body.find("#lo-customer-search").val(), $body.find("#lo-customer-status").val()));
            $body.find("#lo-customer-status").on("change", () => renderCustomers($body.find("#lo-customer-search").val(), $body.find("#lo-customer-status").val()));
        }
    });
};
