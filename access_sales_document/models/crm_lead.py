from odoo import fields, models,api



class CrmLead(models.Model):
    _inherit = 'crm.lead'

    partner_id = fields.Many2one(
        domain=lambda self: self._get_partner_domain()
    )
   
    def _get_partner_domain(self):
        user = self.env.user

        if (user.has_group('sales_team.group_sale_salesman') or 
            user.has_group('sales_team.group_sale_salesman_all_leads')) and not user.has_group('base.group_system'):
            
            return [('user_id', '=', user.id), ('customer_rank', '>=', 0)]

        elif user.has_group('sales_team.group_sale_manager'):
            return []  

        else:
            return [('customer_rank', '>', 0)]
        
    @api.onchange('partner_id')
    def _onchange_partner_id_set_salesperson(self):
        for lead in self:
            if lead.partner_id and lead.partner_id.user_id:
                lead.user_id = lead.partner_id.user_id
