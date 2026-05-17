# -*- coding: utf-8 -*-
from odoo import _, Command, api, fields, models
from odoo.exceptions import UserError, ValidationError


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
    mostakhlas_proforma_invoice_ids = fields.One2many(
        "account.move",
        "mostakhlas_sale_order_id",
        string="Mostakhlas Proforma Invoices",
    )
    mostakhlas_proforma_invoice_count = fields.Integer(
        string="Proforma Invoices",
        compute="_compute_mostakhlas_proforma_invoice_count",
    )

    @api.depends("mostakhlas_proforma_invoice_ids.state")
    def _compute_mostakhlas_proforma_invoice_count(self):
        for order in self:
            order.mostakhlas_proforma_invoice_count = len(
                order.mostakhlas_proforma_invoice_ids.filtered(
                    lambda move: move.state == "draft"
                    and move.is_sale_mostakhlas_proforma
                )
            )

    @api.depends("order_line.invoice_lines", "mostakhlas_proforma_invoice_ids.state")
    def _get_invoiced(self):
        for order in self:
            regular_invoices = order.order_line.invoice_lines.move_id.filtered(
                lambda move: move.move_type in ("out_invoice", "out_refund")
                and move.state == "posted"
            )
            posted_mostakhlas_invoices = order.mostakhlas_proforma_invoice_ids.filtered(
                lambda move: move.state == "posted"
                and move.is_sale_mostakhlas_proforma
            )
            invoices = regular_invoices | posted_mostakhlas_invoices
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

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
            existing_sale_lines = set(order.mostakhlas_line_ids.mapped("sale_line_id").ids)
            existing_unlinked_products = set(
                order.mostakhlas_line_ids.filtered(
                    lambda mostakhlas_line: not mostakhlas_line.sale_line_id
                ).mapped("product_id").ids
            )
            seq = len(order.mostakhlas_line_ids)
            new_vals = []
            for line in order.order_line.filtered(lambda l: not l.display_type):
                if line.id in existing_sale_lines:
                    continue
                if line.product_id.id in existing_unlinked_products:
                    continue
                seq += 1
                new_vals.append({
                    "order_id": order.id,
                    "sale_line_id": line.id,
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

    def _get_selected_mostakhlas_invoice_lines(self):
        self.ensure_one()
        selected = self.mostakhlas_line_ids.filtered(lambda line: line.print_in_report)
        if not selected:
            raise UserError(_("Please select at least one Mostakhlas line."))
        invalid_lines = selected.filtered(lambda line: (line.progress_percent or 0.0) <= 0.0)
        if invalid_lines:
            raise UserError(_("Current Progress %% must be greater than 0 for selected lines."))
        return selected

    def _find_mostakhlas_sale_line(self, mostakhlas_line):
        self.ensure_one()
        sale_line = mostakhlas_line.sale_line_id
        if sale_line and sale_line.order_id == self:
            return sale_line
        return self.order_line.filtered(
            lambda line: not line.display_type
            and line.product_id == mostakhlas_line.product_id
        )[:1]

    def _prepare_mostakhlas_invoice_line_vals(self, mostakhlas_line, sequence):
        self.ensure_one()
        sale_line = self._find_mostakhlas_sale_line(mostakhlas_line)
        invoice_qty = (mostakhlas_line.product_qty or 0.0) * (
            (mostakhlas_line.progress_percent or 0.0) / 100.0
        )
        if sale_line:
            vals = sale_line._prepare_invoice_line(sequence=sequence)
            vals.pop("sale_line_ids", None)
            vals.update({
                "quantity": invoice_qty,
                "name": mostakhlas_line.name or vals.get("name"),
                "product_id": mostakhlas_line.product_id.id,
                "product_uom_id": mostakhlas_line.product_uom.id,
                "price_unit": mostakhlas_line.price_unit,
                "discount": mostakhlas_line.discount,
                "tax_ids": [Command.set(mostakhlas_line.taxes_id.ids)],
            })
            if mostakhlas_line.analytic_distribution:
                vals["analytic_distribution"] = mostakhlas_line.analytic_distribution
            return vals
        return {
            "display_type": "product",
            "sequence": sequence,
            "name": mostakhlas_line.name or mostakhlas_line.product_id.display_name,
            "product_id": mostakhlas_line.product_id.id,
            "product_uom_id": mostakhlas_line.product_uom.id,
            "quantity": invoice_qty,
            "price_unit": mostakhlas_line.price_unit,
            "discount": mostakhlas_line.discount,
            "tax_ids": [Command.set(mostakhlas_line.taxes_id.ids)],
            "analytic_distribution": mostakhlas_line.analytic_distribution,
        }

    def _create_mostakhlas_proforma_invoice(self):
        self.ensure_one()
        selected = self._get_selected_mostakhlas_invoice_lines()

        invoice_vals = self._prepare_invoice()
        invoice_vals.update({
            "move_type": "out_invoice",
            "is_sale_mostakhlas_proforma": True,
            "mostakhlas_sale_order_id": self.id,
            "invoice_line_ids": [],
        })
        for sequence, mostakhlas_line in enumerate(selected, start=1):
            invoice_vals["invoice_line_ids"].append(
                Command.create(
                    self._prepare_mostakhlas_invoice_line_vals(mostakhlas_line, sequence)
                )
            )

        invoice = self.env["account.move"].sudo().with_context(
            default_move_type="out_invoice",
            move_type="out_invoice",
            arka_mostakhlas_proforma=True,
        ).create(invoice_vals)
        selected.write({"print_in_report": False})
        invoice.message_post_with_source(
            "mail.message_origin_link",
            render_values={"self": invoice, "origin": self},
            subtype_xmlid="mail.mt_note",
        )
        return invoice

    def action_view_mostakhlas_proforma_invoices(self):
        self.ensure_one()
        invoices = self.mostakhlas_proforma_invoice_ids.filtered(
            lambda move: move.state == "draft"
            and move.is_sale_mostakhlas_proforma
        )
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        action["context"] = {
            "default_move_type": "out_invoice",
            "default_partner_id": self.partner_id.id,
            "default_partner_shipping_id": self.partner_shipping_id.id,
        }
        return action

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
            # if pct <= 0:
            #     raise ValidationError(
            #         f"Progress % for line {line.sequence_int} must be greater than 0."
            #     )
            new_done = (line.done_progress or 0.0) + pct
            # if new_done > 100:
            #     raise ValidationError(
            #         f"Total progress for line {line.sequence_int} exceeds 100%."
            #     )
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
