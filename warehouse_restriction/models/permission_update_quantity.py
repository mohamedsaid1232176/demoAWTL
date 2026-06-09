from odoo import models, api, fields, SUPERUSER_ID,_
from odoo.exceptions import ValidationError,UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_update_quantity_on_hand(self):
        user = self.env.user

        # Check if user is Inventory Administrator
        if not user.has_group("stock.group_stock_manager"):
            raise UserError(_("You do not have permission to update quantity. Only Inventory Administrators can perform this action."))

        # Otherwise, allow normal behavior
        return super(ProductTemplate, self).action_update_quantity_on_hand()




class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def action_apply_all(self):
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise UserError("You are not allowed to apply inventory adjustments.")
        return super().action_apply_all()

    def action_apply_inventory(self):
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise UserError("You are not allowed to apply inventory quantity.")
        return super().action_apply_inventory()