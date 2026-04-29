# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # ══════════════════════════════════════════════════
    #                   SEQUENCE
    # ══════════════════════════════════════════════════
    mostakhlas_sequence = fields.Char(
        string="Mostakhlas No.",
        readonly=True,
        copy=False,
        default="SMO-0",
    )

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if not order.mostakhlas_sequence:
                order.mostakhlas_sequence = "SMO-0"
        return orders

    # ══════════════════════════════════════════════════
    #                    FLAGS
    # ══════════════════════════════════════════════════
    show_mostakhlas_tab = fields.Boolean(default=False)

    # ══════════════════════════════════════════════════
    #                  RELATIONS
    # ══════════════════════════════════════════════════
    mostakhlas_line_ids = fields.One2many(
        "sale.mostakhlas.line", "order_id", string="Mostakhlas Lines"
    )

    sale_payment_ids = fields.Many2many(
        "account.payment",
        "sale_order_payment_rel",
        "order_id",
        "payment_id",
        string="Customer Payments",
        domain=[
            ("state", "=", "posted"),
            ("partner_type", "=", "customer"),
            ("payment_type", "=", "inbound"),
        ],
    )

    project_id = fields.Many2one("project.project", string="Project")

    # ══════════════════════════════════════════════════
    #                 CURRENCY
    # ══════════════════════════════════════════════════
    mostakhlas_currency_id = fields.Many2one(
        related="company_id.currency_id",
        readonly=True,
        string="Currency",
    )

    # ══════════════════════════════════════════════════
    #                  TOTALS
    # ══════════════════════════════════════════════════
    mostakhlas_untaxed = fields.Monetary(
        string="Untaxed Amount",
        compute="_compute_mostakhlas_totals",
        store=True,
        currency_field="mostakhlas_currency_id",
    )
    mostakhlas_tax = fields.Monetary(
        string="VAT (15%)",
        compute="_compute_mostakhlas_totals",
        store=True,
        currency_field="mostakhlas_currency_id",
    )
    mostakhlas_total = fields.Monetary(
        string="Total",
        compute="_compute_mostakhlas_totals",
        store=True,
        currency_field="mostakhlas_currency_id",
    )
    executed_contract_value = fields.Monetary(
        string="إجمالي قيمة الأعمال التعاقدية المنفذة",
        compute="_compute_mostakhlas_executed",
        store=True,
        currency_field="mostakhlas_currency_id",
    )
    executed_contract_value_vat = fields.Monetary(
        string="إجمالي قيمة الأعمال المنفذة شامل ضريبة القيمة المضافة",
        compute="_compute_mostakhlas_executed",
        store=True,
        currency_field="mostakhlas_currency_id",
    )

    # ── Customer Payments ───────────────────────────
    sale_payment_total = fields.Monetary(
        string="Total Customer Payments",
        compute="_compute_sale_payment_total",
        store=True,
        currency_field="mostakhlas_currency_id",
    )
    sale_payment_total_paid = fields.Monetary(
        string="Total Collected Payments",
        compute="_compute_sale_payment_total_paid",
        store=True,
        currency_field="mostakhlas_currency_id",
    )
    sale_payment_total_paid_in_mostakhlas = fields.Monetary(
        string="Payments in This Mostakhlas",
        compute="_compute_sale_payment_total_paid_in_mostakhlas",
        store=True,
        currency_field="mostakhlas_currency_id",
    )
    sale_payment_total_all = fields.Monetary(
        string="Total Collected Payments",
        compute="_compute_sale_payment_total_all",
        store=True,
        currency_field="mostakhlas_currency_id",
    )

    # ══════════════════════════════════════════════════
    #    IMPORTANT DATA FIELDS
    # ══════════════════════════════════════════════════
    # computed from project
    project_manager = fields.Char(
        string="Project Manager",
        compute="_compute_project_manager",
        store=True,
    )

    @api.depends("project_id", "project_id.user_id")
    def _compute_project_manager(self):
        for rec in self:
            rec.project_manager = (
                rec.project_id.user_id.name
                if rec.project_id and rec.project_id.user_id
                else False
            )

    operations_manager = fields.Char(
        string="Operations Manager",
        default="مصطفى شاهين",
    )

    # اسم العميل — محسوب من partner_id
    client_name = fields.Char(
        string="Client Name",
        compute="_compute_client_name",
        store=True,
    )

    @api.depends("partner_id")
    def _compute_client_name(self):
        for rec in self:
            rec.client_name = rec.partner_id.name if rec.partner_id else False

    date_mostakhlas = fields.Date(string="Mostakhlas Date")
    date_client = fields.Date(string="Date")

    # ══════════════════════════════════════════════════
    #   COMPUTE TOTALS — buffer-based
    # ══════════════════════════════════════════════════
    @api.depends(
        "mostakhlas_line_ids.price_subtotal",
        "mostakhlas_line_ids.taxes_id",
        "mostakhlas_line_ids.product_qty",
        "mostakhlas_line_ids.price_unit",
    )
    def _compute_mostakhlas_totals(self):
        for order in self:
            untaxed = tax = 0.0
            buffer_lines = self.env["sale.mostakhlas.print.buffer"].search(
                [("order_id", "=", order.id)]
            ).mapped("line_id")
            lines = buffer_lines or order.mostakhlas_line_ids

            for line in lines:
                untaxed += line.price_subtotal
                if line.taxes_id:
                    taxes_res = line.taxes_id.compute_all(
                        line.price_unit,
                        currency=order.mostakhlas_currency_id,
                        quantity=line.product_qty,
                        product=line.product_id,
                        partner=order.partner_id,
                    )
                    tax += sum(t["amount"] for t in taxes_res["taxes"])

            order.mostakhlas_untaxed = untaxed
            order.mostakhlas_tax = tax
            order.mostakhlas_total = untaxed + tax

    @api.depends(
        "mostakhlas_line_ids.product_qty",
        "mostakhlas_line_ids.price_unit",
        "mostakhlas_line_ids.taxes_id",
        "mostakhlas_line_ids.progress_percent",
        "mostakhlas_line_ids.done_progress",
    )
    def _compute_mostakhlas_executed(self):
        for order in self:
            exec_untaxed = exec_total = 0.0
            buffer_lines = self.env["sale.mostakhlas.print.buffer"].search(
                [("order_id", "=", order.id)]
            ).mapped("line_id")
            lines = buffer_lines or order.mostakhlas_line_ids

            for line in lines:
                qty = line.product_qty or 0.0
                price = line.price_unit or 0.0
                total_progress = (line.done_progress or 0.0) / 100.0
                line_untaxed = qty * price
                exec_line = line_untaxed * total_progress
                exec_untaxed += exec_line
                exec_total += exec_line * 1.15 if line.taxes_id else exec_line

            order.executed_contract_value = exec_untaxed
            order.executed_contract_value_vat = exec_total

    # ── Payment computes ────────────────────────────
    @api.depends("sale_payment_ids", "sale_payment_ids.amount", "sale_payment_ids.state")
    def _compute_sale_payment_total(self):
        for order in self:
            order.sale_payment_total = sum(
                order.sale_payment_ids.filtered(
                    lambda p: p.state not in ("cancel", "draft")
                ).mapped("amount")
            )

    @api.depends("sale_payment_ids", "sale_payment_ids.amount", "sale_payment_ids.state")
    def _compute_sale_payment_total_paid(self):
        for order in self:
            order.sale_payment_total_paid = sum(
                order.sale_payment_ids.filtered(lambda p: p.state == "posted").mapped("amount")
            )

    @api.depends("sale_payment_ids", "sale_payment_ids.amount",
                 "sale_payment_ids.state", "sale_payment_ids.is_used_in_sale_mostakhlas")
    def _compute_sale_payment_total_paid_in_mostakhlas(self):
        for order in self:
            new_payments = order.sale_payment_ids.filtered(
                lambda p: p.state == "posted" and not p.is_used_in_sale_mostakhlas
            )
            if not order.sale_payment_ids.filtered(lambda p: p.is_used_in_sale_mostakhlas):
                new_payments = order.sale_payment_ids.filtered(lambda p: p.state == "posted")
            order.sale_payment_total_paid_in_mostakhlas = sum(new_payments.mapped("amount"))

    @api.depends("sale_payment_ids", "sale_payment_ids.amount", "sale_payment_ids.state")
    def _compute_sale_payment_total_all(self):
        for order in self:
            order.sale_payment_total_all = sum(
                order.sale_payment_ids.filtered(
                    lambda p: p.state in ("posted", "paid")
                ).mapped("amount")
            )

    # ══════════════════════════════════════════════════
    #           OPEN MOSTAKHLAS TAB
    # ══════════════════════════════════════════════════
    def action_open_mostakhlas_tab(self):
        for order in self:
            existing = set(order.mostakhlas_line_ids.mapped("product_id").ids)
            seq = len(order.mostakhlas_line_ids)
            new_vals = []
            for line in order.order_line.filtered(lambda l: not l.display_type):
                if line.product_id.id in existing:
                    continue
                seq += 1
                new_vals.append({
                    "order_id": order.id,
                    "sequence_int": seq,
                    "product_id": line.product_id.id,
                    "name": line.name,
                    "product_qty": line.product_uom_qty,
                    "product_uom": line.product_uom.id,
                    "price_unit": line.price_unit,
                    "discount": line.discount,
                    "taxes_id": [(6, 0, line.tax_id.ids)],
                    "analytic_distribution": line.analytic_distribution,
                })
            if new_vals:
                self.env["sale.mostakhlas.line"].create(new_vals)
            order.show_mostakhlas_tab = True
        return True

    # ══════════════════════════════════════════════════
    #           PRINT MOSTAKHLAS
    # ══════════════════════════════════════════════════
    def action_print_sale_mostakhlas(self):
        try:
            num = int((self.mostakhlas_sequence or "SMO-0").replace("SMO-", "")) + 1
        except Exception:
            num = 1
        self.mostakhlas_sequence = f"SMO-{num}"

        selected = self.mostakhlas_line_ids.filtered(lambda l: l.print_in_report)
        if not selected:
            raise ValidationError("Please select at least one line to print.")

        for line in selected:
            pct = line.progress_percent or 0.0
            if pct <= 0:
                raise ValidationError(
                    f"Progress % for line {line.sequence_int} must be greater than 0."
                )
            new_done = (line.done_progress or 0.0) + pct
            if new_done > 100:
                raise ValidationError(
                    f"Total progress for line {line.sequence_int} exceeds 100%."
                )
            line.done_progress = new_done

        self.env["sale.mostakhlas.print.buffer"].search(
            [("order_id", "=", self.id)]
        ).unlink()
        for line in selected:
            self.env["sale.mostakhlas.print.buffer"].create({
                "order_id": self.id,
                "line_id": line.id,
            })

        action = self.env.ref(
            "arka_mostakhlas.action_report_sale_mostakhlas"
        ).report_action(self)

        selected.write({"print_in_report": False})

        paid = self.sale_payment_ids.filtered(lambda p: p.state in ("posted", "paid"))
        new_payments = paid.filtered(lambda p: not p.is_used_in_sale_mostakhlas)
        if not paid.filtered(lambda p: p.is_used_in_sale_mostakhlas):
            new_payments = paid
        new_payments.write({"is_used_in_sale_mostakhlas": True})

        return action

    # ══════════════════════════════════════════════════
    #              OPEN WIZARD
    # ══════════════════════════════════════════════════
    def action_open_sale_mostakhlas_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.mostakhlas.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_id": self.id},
        }

    # ══════════════════════════════════════════════════
    #              CONSTRAINTS
    # ══════════════════════════════════════════════════
    @api.constrains("sale_payment_ids")
    def _check_sale_payments_amount(self):
        for order in self:
            total_paid = sum(order.sale_payment_ids.mapped("amount"))
            limit = order.mostakhlas_untaxed or 0.0
            if limit > 0 and total_paid > limit:
                raise ValidationError(
                    f"Total customer payments ({total_paid:.2f}) "
                    f"cannot exceed the mostakhlas value ({limit:.2f})."
                )
