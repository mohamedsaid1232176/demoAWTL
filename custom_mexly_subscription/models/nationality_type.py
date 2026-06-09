from odoo import models, fields, api

class NationalityType(models.Model):
    _name = 'nationality.type'
    _description = 'Nationality Type'


    name = fields.Char(string="Name")