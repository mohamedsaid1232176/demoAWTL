from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_role = fields.Selection([
        ('vendor', 'Vendor'),
        ('customer', 'Customer'),
        ('employee', 'Employee'),
    ], string="Partner Role", required=True)

    employee_type = fields.Selection(
        [
            ('custody', 'Custody'),
            ('loan', 'Loans'),
            ('payroll', 'Payroll'),
        ],
        string="Employee Type"
    )

    partner_ref = fields.Char(
        string="Partner Reference",
        readonly=True,
        copy=False
    )

    @api.model
    def create(self, vals):

        if not vals.get('partner_ref'):
            seq_code = self._get_sequence_code(vals)
            if seq_code:
                vals['partner_ref'] = self.env['ir.sequence'].next_by_code(seq_code)


        if vals.get('partner_ref'):
            vals['ref'] = vals['partner_ref']

        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)

        for partner in self:
            if not partner.partner_ref:
                partner._assign_partner_ref()

            if partner.partner_ref and partner.ref != partner.partner_ref:
                partner.ref = partner.partner_ref


        return res

    def _get_sequence_code(self, vals):
        partner_role = vals.get('partner_role')
        employee_type = vals.get('employee_type')

        if partner_role == 'employee' and employee_type:
            seq_map = {
                'custody': 'employee.custody',
                'loan': 'employee.loan',
                'payroll': 'employee.payroll',
            }
            return seq_map.get(employee_type)

        if partner_role == 'employee':
            return 'partner.employee'

        if partner_role == 'customer':
            return 'partner.customer'

        if partner_role == 'vendor':
            return 'partner.vendor'

        return False

    def _assign_partner_ref(self):
        for partner in self:
            if partner.partner_ref:
                continue

            seq_code = partner._get_sequence_code({
                'partner_role': partner.partner_role,
                'employee_type': partner.employee_type,
            })

            if seq_code:
                new_ref = self.env['ir.sequence'].next_by_code(seq_code)
                partner.partner_ref = new_ref
                partner.ref = new_ref   