from odoo import models, api, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'


    @api.model
    def create(self, vals):
        if 'user_id' not in vals or not vals['user_id']:
            vals['user_id'] = self.env.uid
        return super(ResPartner, self).create(vals)
