from odoo import models, fields, api


class PurchaseMostakhlasLine(models.Model):
    _name = "purchase.mostakhlas.line"
    _description = "Purchase Mostakhlas Line"
    _order = "sequence_int, id"


    previous_progress = fields.Float(
        string="Previous Progress (%)",
        compute="_compute_previous_progress",
        store=False
    )

    @api.depends("done_progress", "progress_percent")
    def _compute_previous_progress(self):
        for line in self:
            line.previous_progress = (line.done_progress or 0.0) - (line.progress_percent or 0.0)

    progress_percent = fields.Float(
        string="Progress (%)",
        default=0.0
    )

    order_id = fields.Many2one(
        "purchase.order",
        required=True,
        ondelete="cascade"
    )

    # ===== REAL SEQUENCE NUMBER =====
    sequence_int = fields.Integer(
        string="Line Number",
        store=True
    )

    # ===== RELATED (FOR DEPENDS) =====
    vendor_id = fields.Many2one(
        related="order_id.partner_id",
        store=True
    )

    project_id = fields.Many2one(
        related="order_id.project_id",
        store=True
    )

    mostakhlas_type_id = fields.Many2one(
        "mostakhlas.type",
        string="Mostakhlas Type"
    )

    # ===== NORMAL FIELDS =====
    product_id = fields.Many2one("product.product", string="Product")
    name = fields.Text(string="Description")
    date_planned = fields.Datetime(string="Expected Arrival")

    product_qty = fields.Float(string="Quantity", default=1.0)
    product_uom = fields.Many2one("uom.uom", string="UoM")

    price_unit = fields.Float(string="Unit Price", default=0.0)
    discount = fields.Float(string="Disc.%")

    taxes_id = fields.Many2many("account.tax", string="Taxes")

    currency_id = fields.Many2one(
        related="order_id.currency_id",
        store=True,
        readonly=True
    )

    price_subtotal = fields.Monetary(
        string="Amount",
        currency_field="currency_id",
        compute="_compute_price_subtotal",
        store=True
    )

    analytic_distribution = fields.Json(string="Analytic Distribution")

    propagate_cancel = fields.Boolean(string="Propagate cancellation")

    # ===== COMPUTE AMOUNT =====
    @api.depends("product_qty", "price_unit", "discount")
    def _compute_price_subtotal(self):
        for line in self:
            qty = line.product_qty or 0.0
            price = line.price_unit or 0.0
            discount = line.discount or 0.0

            subtotal = qty * price
            if discount:
                subtotal -= subtotal * (discount / 100)

            line.price_subtotal = subtotal

    # انشاء field checkbox

    print_in_report = fields.Boolean(string="Print in Report", default=False)
    done_progress = fields.Float(
        string=" Progress Done (%)",
        default=0.0
    )

    # لو وصلت نسبة الإنجاز 100 → خلي progress_percent read-
    is_progress_locked = fields.Boolean(
        compute="_compute_is_progress_locked",
        store=False
    )

    @api.depends("done_progress")
    def _compute_is_progress_locked(self):
        for line in self:
            line.is_progress_locked = line.done_progress >= 100


class MostakhlasType(models.Model):
    _name = "mostakhlas.type"
    _description = "Mostakhlas Type"

    name = fields.Char(string="نوع المستخلص", required=True)


class ResPartner(models.Model):
    _inherit = "res.partner"

    total_all_due = fields.Monetary(
        string="إجمالي المديونية",
        currency_field="currency_id",
        store=False
    )

    has_moves = fields.Boolean(
        string="Has Moves",
        store=False
    )


class MostakhlasPrintBuffer(models.Model):
    _name = "mostakhlas.print.buffer"
    _description = "Buffered Lines For Mostakhlas Printing"

    line_id = fields.Many2one("purchase.mostakhlas.line", required=True)
    order_id = fields.Many2one("purchase.order", required=True)


