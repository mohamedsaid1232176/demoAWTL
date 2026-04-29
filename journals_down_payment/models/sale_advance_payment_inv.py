import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def _create_invoices(self, sale_orders):
        _logger.info(">>> دخلنا جوه _create_invoices في Odoo 18")

        invoices = super()._create_invoices(sale_orders)
        _logger.info(">>> اتعملت الفواتير: %s", invoices)

        # نجيب الـ Journal اللي معمول له Down Payment = True
        journal = self.env['account.journal'].search([('down_payment', '=', True)], limit=1)
        if not journal:
            _logger.warning(">>> مفيش Journal معمول له Down Payment = True")
            raise UserError("لا يوجد Journal معمول له Down Payment = True")
        _logger.info(">>> لقينا الـ Journal: %s", journal.name)

        for invoice in invoices:
            invoice.journal_id = journal.id
            _logger.info(">>> غيّرنا journal_id بتاع الفاتورة إلى: %s", journal.name)

            if journal.default_account_id:
                invoice.invoice_line_ids.write({
                    'account_id': journal.default_account_id.id
                })
                _logger.info(">>> اتغير account_id لكل invoice lines إلى: %s", journal.default_account_id.display_name)

        return invoices


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def action_view_downpayments(self):
        line = self[0]  # خُد أول واحد بس
        return {
            "name": "Customer Down Payments",
            "type": "ir.actions.act_window",
            "res_model": "customer.downpayment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": line.partner_id.id,
                "default_invoice_id": line.move_id.id,
            },
        }


class CustomerDownPaymentWizard(models.TransientModel):
    _name = "customer.downpayment.wizard"
    _description = "Customer Down Payments Wizard"

    partner_id = fields.Many2one("res.partner", string="Customer", readonly=True)
    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True)
    downpayment_ids = fields.Many2many(
        "account.move",
        string="Down Payments",
        domain="[('state','=','posted'),('move_type', '=', 'out_invoice'),('journal_id.down_payment', '=', True),('partner_id', '=', partner_id)]")

    def action_add_to_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError("لا توجد فاتورة لإضافة السطور إليها.")
        if not self.downpayment_ids:
            raise UserError("من فضلك اختر فاتورة Down Payment واحدة على الأقل.")

        line_vals = []
        for dp in self.downpayment_ids:
            dp_line = dp.invoice_line_ids[0]  # خُد أول سطر بس
            line_vals.append((0, 0, {
                'product_id': dp_line.product_id.id,
                'name': dp_line.name or dp.ref or 'Down Payment',
                'quantity': -dp_line.quantity if dp_line.quantity > 0 else dp_line.quantity or -1.0,
                'price_unit': dp_line.price_unit,
                'tax_ids': [(6, 0, dp_line.tax_ids.ids)],
                'account_id': dp_line.account_id.id,
            }))

        if line_vals:
            self.invoice_id.write({'invoice_line_ids': line_vals})
        return {'type': 'ir.actions.act_window_close'}
