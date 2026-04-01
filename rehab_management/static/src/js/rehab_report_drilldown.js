/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { ajax } from "@web/core/network/ajax";

publicWidget.registry.RehabReportDrilldown = publicWidget.Widget.extend({
    selector: '.o_account_reports_page',
    events: {
        'click .o_account_reports_web_action': '_onDrillDown',
        'click .o_account_report_caret': '_onToggleGroup',
    },

    _onToggleGroup: function (ev) {
        ev.stopPropagation();
        const $caret = $(ev.currentTarget);
        const $row = $caret.closest('tr');
        const groupName = $row.data('group-name');
        
        $caret.toggleClass('caret_open');
        this.$('.o_account_report_table tr[data-parent-group="' + groupName + '"]').toggleClass('row_hidden');
    },

    _onDrillDown: function (ev) {
        ev.preventDefault();
        const $target = $(ev.currentTarget);
        const domainStr = $target.attr('data-domain');
        const resModel = $target.attr('data-res-model') || 'account.move.line';
        
        if (!domainStr) return;

        try {
            const domain = JSON.parse(domainStr);
            this.do_action({
                type: 'ir.actions.act_window',
                name: $target.text().trim(),
                res_model: resModel,
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                context: {
                    'search_default_posted': 1,
                    // Rehab context
                    'rehab_drilldown': true,
                }
            });
        } catch (e) {
            console.error("Failed to parse drill-down domain:", e);
        }
    },
});

export default publicWidget.registry.RehabReportDrilldown;
