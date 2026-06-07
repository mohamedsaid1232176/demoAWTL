from odoo import models, fields, api


class TitleDeedType(models.Model):
    _name = 'title.deed.type'
    _description = 'Title Deed Type'

    name = fields.Char(string="Name", required=True)