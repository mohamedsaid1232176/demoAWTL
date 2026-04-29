from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    parent_payment_id = fields.Many2one(
        "account.payment",
        string="Parent Payment",
        readonly=True,
        ondelete="cascade"
    )

    child_payment_ids = fields.One2many(
        "account.payment",
        "parent_payment_id",
        string="Related Payments"
    )

    is_child_payment = fields.Boolean(
        string="Is Child Payment",
        default=False,
    )

    def write(self, vals):
        propagate_state = self.env.context.get('propagate_request_state', False)

        res = super().write(vals)

        if 'request_state' in vals and not propagate_state:
            for rec in self:
                if rec.child_payment_ids:
                    rec.child_payment_ids.with_context(propagate_request_state=True).write({
                        'request_state': vals['request_state']
                    })
            for rec in self:
                if rec.parent_payment_id:
                    rec.parent_payment_id.with_context(propagate_request_state=True).write({
                        'request_state': vals['request_state']
                    })

        return res



  
    @api.model
    def create(self, vals):

        if vals.get("parent_payment_id"):
            vals['is_child_payment'] = True
            parent = self.env['account.payment'].search([('id', '=', vals['parent_payment_id'])], limit=1)
            if not parent:
                raise ValidationError("Parent payment does not exist.")
        
        payment = super().create(vals)

        # لو child payment
        if payment.parent_payment_id:
            parent = payment.parent_payment_id

            payment.write({
                "partner_id": parent.partner_id.id,
                "employee_id": parent.employee_id.id,
                "department_id": parent.department_id.id,
                "custom_sequence": parent.custom_sequence,
                "company_id": parent.company_id.id,
                "request_state": parent.request_state,

                # الحقول اللي ما جاتش من الـ context
                "payment_type": parent.payment_type,
                "partner_type": parent.partner_type,
                "journal_id": parent.journal_id.id,
                "payment_method_line_id": parent.payment_method_line_id.id,
                "partner_bank_id": parent.partner_bank_id.id,
                "currency_id": parent.currency_id.id,
            })

        return payment
    

    

