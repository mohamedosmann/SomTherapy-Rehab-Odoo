/** @odoo-module **/
/**
 * rehab_report_drilldown.js
 *
 * OWL 2.x patch that listens for clicks on elements carrying the
 * class "rh-drilldown" inside any rendered HTML report.
 *
 * On click it:
 *   1. Reads data-account-id, data-date-from, data-date-to,
 *      data-company-id from the element (all set by QWeb).
 *   2. POSTs those values to /rehab_management/report/drilldown.
 *   3. Calls this.env.services.action.doAction(response) so the
 *      filtered journal-items list opens *inside* the Odoo SPA —
 *      each row then links to its source document (invoice/payment).
 *   4. Shows a subtle loading spinner on the cell while waiting.
 *   5. Displays a notification toast on error.
 */

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { ReportAction } from "@web/webclient/actions/reports/report_action";

// ─── helper ────────────────────────────────────────────────────────────────

async function postDrilldown(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            id: Math.floor(Math.random() * 1e9),
            params: payload,
        }),
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    const json = await response.json();
    if (json.error) {
        throw new Error(json.error.data?.message || json.error.message || "RPC error");
    }
    return json.result;
}

// ─── patch ReportAction ─────────────────────────────────────────────────────

patch(ReportAction.prototype, {
    setup() {
        super.setup(...arguments);
        this._actionService = useService("action");
        this._notifService = useService("notification");
    },

    /**
     * Attach a delegated click handler to the report iframe's document
     * every time the iframe content is (re-)loaded.
     */
    _onIframeLoad(iframe) {
        // Call the original hook if it exists
        if (super._onIframeLoad) {
            super._onIframeLoad(...arguments);
        }
        const doc = iframe?.contentDocument || iframe?.contentWindow?.document;
        if (!doc) return;

        doc.addEventListener("click", (ev) => {
            const el = ev.target.closest(".rh-drilldown");
            if (!el) return;

            ev.preventDefault();
            ev.stopPropagation();

            // ── loading state ──────────────────────────────────────────────
            const originalHtml = el.innerHTML;
            el.style.opacity = "0.5";
            el.style.pointerEvents = "none";
            el.setAttribute("aria-busy", "true");

            const payload = {
                account_id: el.dataset.accountId ? parseInt(el.dataset.accountId) : null,
                date_from: el.dataset.dateFrom || null,
                date_to: el.dataset.dateTo || null,
                company_id: el.dataset.companyId ? parseInt(el.dataset.companyId) : null,
            };

            postDrilldown("/rehab_management/report/drilldown", payload)
                .then((action) => {
                    // ── restore cell ───────────────────────────────────────
                    el.style.opacity = "";
                    el.style.pointerEvents = "";
                    el.removeAttribute("aria-busy");

                    // ── open journal items inside Odoo SPA ─────────────────
                    this._actionService.doAction(action, {
                        clearBreadcrumbs: false,
                    });
                })
                .catch((err) => {
                    el.style.opacity = "";
                    el.style.pointerEvents = "";
                    el.removeAttribute("aria-busy");

                    this._notifService.add(
                        `Could not load journal items: ${err.message}`,
                        { type: "danger", sticky: false }
                    );
                });
        });
    },
});
