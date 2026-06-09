from odoo import fields, models,api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    partner_id = fields.Many2one(domain=lambda self: self._get_partner_domain())

    user_id = fields.Many2one('res.users',string='Salesperson',default=lambda self: self.env.user)

    def _get_partner_domain(self):
        user = self.env.user

        # ✅ الأول تحقق من Manager
        if user.has_group('sales_team.group_sale_manager'):
            return []

        # ثم Salesperson
        elif (user.has_group('sales_team.group_sale_salesman') or
              user.has_group('sales_team.group_sale_salesman_all_leads')):

            return [
                ('user_id', '=', user.id),
                ('customer_rank', '>=', 0)
            ]

        else:
            return [('customer_rank', '>', 0)]


    @api.model
    def create(self, vals):
        user = self.env.user
        if 'user_id' in vals and not user.has_group('sales_team.group_sale_manager'):
            if vals['user_id'] != user.id:
                raise ValidationError("You are not allowed to change the salesperson.")
         
        if not vals.get('user_id'):
            vals['user_id'] = user.id
        return super().create(vals)

    def write(self, vals):
        user = self.env.user
        if 'user_id' in vals and not user.has_group('sales_team.group_sale_manager'):
            if any(self.browse(record.id).user_id.id != vals['user_id'] and vals['user_id'] != user.id for record in self):
                raise ValidationError("You are not allowed to change the salesperson.")
        return super().write(vals)