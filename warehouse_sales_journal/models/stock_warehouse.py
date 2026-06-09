from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"


    @api.constrains('journal_id', 'move_type')
    def _check_journal_move_type(self):
        for move in self:
            # ✅ اسمح بالـ Draft من غير Journal
            if move.state == 'draft' and not move.journal_id:
                continue

            # ✅ Purchase documents
            if (
                    move.is_purchase_document(include_receipts=True)
                    and move.journal_id
                    and move.journal_id.type != 'purchase'
            ):
                raise ValidationError(
                    _("Cannot create a purchase document in a non purchase journal")
                )

            # ✅ Sale documents
            if (
                    move.is_sale_document(include_receipts=True)
                    and move.journal_id
                    and move.journal_id.type != 'sale'
            ):
                raise ValidationError(
                    _("Cannot create a sale document in a non sale journal")
                )

    @api.depends('move_type', 'company_id')
    def _compute_journal_id(self):
        # ❌ متعملش أي auto-assign
        # journal يتحط بس من business logic (Sale Order)
        return

    def action_post(self):
        for move in self:
            if move.move_type in ("out_invoice", "out_refund"):
                if not move.journal_id or move.journal_id.type != "sale":
                    raise ValidationError(
                        "Please select a Sales Journal before posting the invoice."
                    )
        return super().action_post()

    @api.onchange('invoice_origin')
    def _onchange_set_journal_from_sale(self):
        if self.move_type != 'out_invoice':
            return

        if not self.invoice_origin:
            return

        sale = self.env['sale.order'].search(
            [('name', '=', self.invoice_origin)],
            limit=1
        )
        if sale and sale.warehouse_id.sales_journal_id:
            self.journal_id = sale.warehouse_id.sales_journal_id

    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        compute='_compute_journal_id', inverse='_inverse_journal_id', store=True, readonly=False, precompute=True,
        required=False,
        check_company=True,
        domain="[('id', 'in', suitable_journal_ids)]",
    )

# =====================================================
# Warehouse
# =====================================================
class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    sales_journal_id = fields.Many2one(
        "account.journal",
        string="Sales Journal",
        domain="[('type','=','sale'), ('company_id','=',company_id)]",
        help="Sales journal used for invoices created from this warehouse"
    )


# =====================================================
# Sale Order
# =====================================================
class SaleOrder(models.Model):
    _inherit = "sale.order"

    analytic_distribution_model_id = fields.Many2one(
        "account.analytic.distribution.model",
        compute="_compute_analytic_distribution_model",
        store=True,
        readonly=True
    )

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()

        # لو الـ Warehouse عليه Sales Journal → استخدمه
        if self.warehouse_id and self.warehouse_id.sales_journal_id:
            vals["journal_id"] = self.warehouse_id.sales_journal_id.id

        # ❌ لو مفيش Journal → سيبه فاضي (مفيش Error)
        return vals

    @api.depends("warehouse_id")
    def _compute_analytic_distribution_model(self):
        for order in self:
            order.analytic_distribution_model_id = False
            journal = order.warehouse_id.sales_journal_id
            if journal:
                order.analytic_distribution_model_id = self.env[
                    "account.analytic.distribution.model"
                ].search(
                    [
                        ("sales_journal_id", "=", journal.id),
                        ("product_id", "=", False),
                        ("partner_id", "=", False),
                        ("account_prefix", "=", False),
                        ("user_id", "=", False),
                    ],
                    limit=1
                )

    def _get_salesperson_analytic_model(self):
        self.ensure_one()
        if not self.user_id:
            return False

        return self.env["account.analytic.distribution.model"].search(
            [
                ("user_id", "=", self.user_id.id),
                ("sales_journal_id", "=", False),
                ("product_id", "=", False),
            ],
            limit=1
        )

    @api.onchange("warehouse_id", "user_id")
    def _onchange_apply_analytic(self):
        self._apply_analytic_to_all_lines()

    def _apply_analytic_to_all_lines(self):
        for order in self:
            for line in order.order_line:
                line._apply_analytic_from_order()



# =====================================================
# Analytic Distribution Model
# =====================================================
class AnalyticDistributionModel(models.Model):
    _inherit = "account.analytic.distribution.model"

    sales_journal_id = fields.Many2one(
        "account.journal",
        string="Sales Journal",
        domain="[('type', '=', 'sale')]"
    )

    user_id = fields.Many2one(
        "res.users",
        string="Salesperson"
    )


# =====================================================
# Product
# =====================================================
class ProductTemplate(models.Model):
    _inherit = "product.template"

    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account"
    )


# =====================================================
# Sale Order Line
# =====================================================
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _apply_custom_analytic_workflow(self):
        AnalyticModel = self.env["account.analytic.distribution.model"]

        for line in self:
            distribution = {}

            journal_model = line.order_id.analytic_distribution_model_id
            if journal_model and journal_model.analytic_distribution:
                distribution.update(journal_model.analytic_distribution)

            salesperson_model = line.order_id._get_salesperson_analytic_model()
            if salesperson_model and salesperson_model.analytic_distribution:
                for acc_id, percent in salesperson_model.analytic_distribution.items():
                    distribution[acc_id] = distribution.get(acc_id, 0.0) + percent

            line.analytic_distribution = distribution or False

    @api.depends('product_id', 'order_id.warehouse_id', 'order_id.user_id')
    def _compute_analytic_distribution(self):
        AnalyticModel = self.env["account.analytic.distribution.model"]

        for line in self:
            distribution = {}

            if not line.product_id:
                line.analytic_distribution = False
                continue

            # 1️⃣ Product Analytic
            product_model = AnalyticModel.search(
                [
                    ("product_id", "=", line.product_id.id),
                    ("sales_journal_id", "=", False),
                    ("user_id", "=", False),
                ],
                limit=1
            )
            if product_model and product_model.analytic_distribution:
                for acc_id, percent in product_model.analytic_distribution.items():
                    distribution[acc_id] = distribution.get(acc_id, 0.0) + percent

            # 2️⃣ Warehouse / Journal
            journal_model = line.order_id.analytic_distribution_model_id
            if journal_model and journal_model.analytic_distribution:
                for acc_id, percent in journal_model.analytic_distribution.items():
                    distribution[acc_id] = distribution.get(acc_id, 0.0) + percent

            # 3️⃣ Salesperson
            salesperson_model = line.order_id._get_salesperson_analytic_model()
            if salesperson_model and salesperson_model.analytic_distribution:
                for acc_id, percent in salesperson_model.analytic_distribution.items():
                    distribution[acc_id] = distribution.get(acc_id, 0.0) + percent

            line.analytic_distribution = distribution or False

    def _apply_analytic_from_order(self):
        AnalyticModel = self.env["account.analytic.distribution.model"]

        for line in self:
            if not line.product_id:
                line.analytic_distribution = False
                continue

            distribution = {}

            # -----------------------------------------
            # 1️⃣ Analytic من Warehouse / Journal
            # -----------------------------------------
            journal_model = line.order_id.analytic_distribution_model_id
            if journal_model and journal_model.analytic_distribution:
                for acc_id, percent in journal_model.analytic_distribution.items():
                    distribution[acc_id] = distribution.get(acc_id, 0.0) + percent

            # -----------------------------------------
            # 2️⃣ Analytic من Product
            # -----------------------------------------
            product_model = AnalyticModel.search(
                [
                    ("product_id", "=", line.product_id.id),
                    ("sales_journal_id", "=", False),
                    ("user_id", "=", False),
                ],
                limit=1
            )

            if product_model and product_model.analytic_distribution:
                for acc_id, percent in product_model.analytic_distribution.items():
                    distribution[acc_id] = distribution.get(acc_id, 0.0) + percent

            # -----------------------------------------
            # 3️⃣ Analytic من Salesperson
            # -----------------------------------------
            salesperson_model = line.order_id._get_salesperson_analytic_model()
            if salesperson_model and salesperson_model.analytic_distribution:
                for acc_id, percent in salesperson_model.analytic_distribution.items():
                    distribution[acc_id] = distribution.get(acc_id, 0.0) + percent

            line.analytic_distribution = distribution or False

    @api.onchange("product_id")
    def _onchange_product_apply_analytic_distribution(self):
        self._apply_analytic_from_order()

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self):
        action = super().create_invoices()

        invoices = self.env["account.move"]

        # الحالة 1️⃣: action فيه res_id (Invoice واحدة)
        if isinstance(action, dict) and action.get("res_id"):
            invoices = self.env["account.move"].browse(action["res_id"])

        # الحالة 2️⃣: action فيه domain (أكتر من Invoice)
        elif isinstance(action, dict) and action.get("domain"):
            invoices = self.env["account.move"].search(action["domain"])

        # أمان إضافي
        invoices = invoices.exists()

        for invoice in invoices:
            for line in invoice.invoice_line_ids:
                if line.sale_line_ids:
                    sale_line = line.sale_line_ids[0]

                    # ✅ انسخ analytic من quotation
                    line.analytic_distribution = sale_line.analytic_distribution or False

        return action
