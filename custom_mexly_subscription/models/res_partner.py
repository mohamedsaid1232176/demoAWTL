from odoo import models, fields,api

class ResPartner(models.Model):

    _inherit = 'res.partner'

    lessor_representative_id = fields.Many2one('lessor.representative', string="ممثل قانوني للمؤجر")

    tenancy_nationality = fields.Char(string="الجنسية")
    tenancy_id_type_id = fields.Many2one('nationality.type', string="نوع الهوية")
    tenancy_id = fields.Char(string="رقم الهوية")