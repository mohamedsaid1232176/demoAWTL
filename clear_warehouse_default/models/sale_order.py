from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['warehouse_id'] = False
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id_clear_warehouse(self):
        """Clear warehouse after selecting a customer."""
        self.warehouse_id = False
