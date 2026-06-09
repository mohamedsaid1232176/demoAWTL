from odoo import models, fields, api


class TaskProductLine(models.Model):
    _name = "task.product.line"
    _description = "Task Product Line"
    _order = "sequence, id"

    # =====================
    # Relations
    # =====================
    task_id = fields.Many2one(
        "project.task",
        string="Task",
        ondelete="cascade",
        required=True
    )

    # =====================
    # Ordering / SI No
    # =====================
    sequence = fields.Integer(
        string="Sequence",
        default=10
    )

    si_no = fields.Integer(
        string="SI No",
        compute="_compute_si_no",
        store=False
    )

    # =====================
    # Product Info
    # =====================
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True
    )

    reference = fields.Char(
        string="Reference",
        related="product_id.default_code",
        store=True
    )

    description = fields.Char(
        string="Description"
    )

    # =====================
    # Quantities
    # =====================
    quantity_ordered = fields.Float(
        string="Quantity Ordered",
        default=1.0
    )

    quantity_transferred = fields.Float(
        string="Quantity Transferred",
        default=0.0,
        readonly=1
    )

    quantity_returned = fields.Float(
        string="Quantity Returned",
        default=0.0,
        readonly=1

    )

    quantity_used = fields.Float(
        string="Quantity Used",
        compute="_compute_quantity_used",
        store=True,
        readonly=1

    )

    # =====================
    # Computes
    # =====================
    @api.depends("quantity_transferred", "quantity_returned")
    def _compute_quantity_used(self):
        for rec in self:
            rec.quantity_used = rec.quantity_transferred - rec.quantity_returned

    @api.depends("task_id.product_line_ids.sequence")
    def _compute_si_no(self):
        """
        Stable SI No numbering per task
        Works correctly with drag & drop
        """
        # نجمع كل الـ tasks المتأثرة
        tasks = self.mapped("task_id")

        for task in tasks:
            lines = task.product_line_ids.sorted(
                key=lambda l: (l.sequence, l.id or 0)
            )
            for index, line in enumerate(lines, start=1):
                line.si_no = index

    # =====================
    # Onchange
    # =====================
    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
