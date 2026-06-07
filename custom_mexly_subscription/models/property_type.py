from odoo import models, fields, api

class PropertyType(models.Model):
    _name = 'property.type'
    _description = 'Property Type'


    name = fields.Char(string="Name")