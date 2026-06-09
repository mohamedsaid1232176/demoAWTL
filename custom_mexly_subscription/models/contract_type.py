from odoo import models, fields, api


class ContractType(models.Model):
    _name = 'contract.type'
    _description = 'Contract Type'

    name = fields.Char(string="Name", required=True)