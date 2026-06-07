from odoo import models, fields, api


class SubscriptionState(models.Model):
    _name = 'subscription.state'
    _description = 'Subscription State'

    name = fields.Char(string='State Name', required=True)
    
    value = fields.Char(string='State Value', required=True)