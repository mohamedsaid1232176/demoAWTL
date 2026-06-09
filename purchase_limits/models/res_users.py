from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    purchase_user_limit = fields.Float(string="Purchase User Limit")
    purchase_manager_from = fields.Float(string="Manager Limit From")
    purchase_manager_to = fields.Float(string="Manager Limit To")
    accounting_limit = fields.Float(string="Finance Manager Limit")
