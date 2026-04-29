from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# -----------------------------
# Journal Down Payment
# -----------------------------
class AccountJournal(models.Model):
    _inherit = 'account.journal'

    down_payment = fields.Boolean(string="Down Payment")

    @api.constrains('down_payment')
    def _check_unique_down_payment(self):
        for rec in self:
            if rec.down_payment:
                other = self.search([
                    ('down_payment', '=', True),
                    ('id', '!=', rec.id)
                ], limit=1)
                if other:
                    raise ValidationError(
                        f"لا يمكن تفعيل 'Down Payment' هنا، لأنه مُفعل بالفعل في الـ Journal: {other.name}"
                    )

# -----------------------------
# Payment Down Payment
# -----------------------------
class AccountPayment(models.Model):
    _inherit = "account.payment"

    down_payment = fields.Boolean(string="Down Payment", default=False)

# -----------------------------
# Account Report Filtering
# -----------------------------

#
# class AccountReport(models.Model):
#     _inherit = "account.report"
#
#     @api.model  # ✅ مهم جدًا عشان يكون callable من RPC
#     def get_down_payment_domain(self):
#         """رجع domain لتصفية الحركات اللي عليها Down Payment"""
#         payment_ids = self.env['account.payment'].search([('down_payment','=',True)]).mapped('id')
#         return [('payment_id','in', payment_ids)]
#
# # -----------------------------
# # Partner Ledger Handler
# # -----------------------------
#
# class PartnerLedgerHandler(models.AbstractModel):
#     _inherit = "account.partner.ledger.report.handler"
#
#     def get_expanded_lines_readonly(self, options, line_id, groupby=None):
#         # استدعاء السلوك الأصلي
#         lines = super().get_expanded_lines_readonly(options, line_id, groupby)
#
#         if not lines:
#             return lines
#
#         # جلب move_ids للمدفوعات اللي عليها down_payment = True
#         payment_move_ids = self.env['account.payment'].search([
#             ('down_payment', '=', True),
#             ('move_id', '!=', False)
#         ]).mapped('move_id').ids
#
#         if not payment_move_ids:
#             return []  # لو مفيش، رجع قائمة فارغة
#
#         # جلب كل move_lines المرتبطة بهذه المدفوعات
#         allowed_ids = self.env['account.move.line'].search([
#             ('move_id', 'in', payment_move_ids)
#         ]).ids
#
#         # فلترة lines
#         filtered_lines = [l for l in lines if l.get("move_line_id") in allowed_ids]
#
#         return filtered_lines
