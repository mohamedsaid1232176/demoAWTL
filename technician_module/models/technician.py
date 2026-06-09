from odoo import models, fields

class Technician(models.Model):
    _name = 'technician.technician'
    _description = 'Technician'

    name = fields.Char(string="Technician Name", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")

class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_name = fields.Char(string="Contact Name")

