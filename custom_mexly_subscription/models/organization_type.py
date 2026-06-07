from odoo import models, fields, api


class OrganizationType(models.Model):
    _name = 'organization.type'
    _description = 'Organization Type'

    name = fields.Char(string="Name", required=True)