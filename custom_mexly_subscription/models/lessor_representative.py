from odoo import models, fields, api


class LessorRepresentative(models.Model):
    _name = 'lessor.representative'
    _description = 'Lessor Representative'

    name = fields.Char(string="Customer Name")