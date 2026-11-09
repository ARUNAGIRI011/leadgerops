frappe.ui.form.on("LedgerOps Exception", {
    refresh(frm) {
        if (frm.is_new() || !frm.has_perm("read")) return;
        const tasks = [
            ["Explain exception", "explain"],
            ["Draft client request", "client_message"],
            ["Reviewer summary", "close_summary"]
        ];
        tasks.forEach(([label, task]) => {
            frm.add_custom_button(__(label), () => {
                frappe.call({
                    method: "ledgerops.ledgerops.api.ai.assist_exception",
                    args: { exception_name: frm.doc.name, task },
                    freeze: true,
                    freeze_message: __("Generating advisory draft…"),
                    callback(r) {
                        if (!r.message) return;
                        const d = new frappe.ui.Dialog({
                            title: __(label),
                            fields: [{ fieldtype: "Small Text", fieldname: "content", label: __("AI draft"), default: r.message.content, read_only: 1 }],
                            primary_action_label: __("Copy"),
                            primary_action(values) {
                                frappe.utils.copy_to_clipboard(values.content);
                                d.hide();
                            }
                        });
                        d.show();
                    }
                });
            }, __("AI Assistant"));
        });
    }
});
