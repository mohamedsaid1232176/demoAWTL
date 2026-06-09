# -*- coding: utf-8 -*-
import base64

from odoo import Command, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_sale_mostakhlas_proforma = fields.Boolean(
        string="Sale Mostakhlas Proforma",
        copy=False,
    )
    mostakhlas_sale_order_id = fields.Many2one(
        "sale.order",
        string="Mostakhlas Sale Order",
        copy=False,
        index=True,
    )
    is_mostakhlas_invoice = fields.Boolean(
        string="Mostakhlas Invoice",
        copy=False,
        readonly=True,
    )
    mostakhlas_number = fields.Char(string="Mostakhlas No.", copy=False)
    mostakhlas_date = fields.Date(string="Mostakhlas Date", copy=False)
    mostakhlas_type = fields.Char(string="Mostakhlas Type", copy=False)
    mostakhlas_pdf_filename = fields.Char(string="PDF Filename", copy=False)
    mostakhlas_pdf = fields.Binary(
        string="Mostakhlas PDF",
        attachment=True,
        copy=False,
    )
    mostakhlas_detail_line_ids = fields.One2many(
        "account.move.mostakhlas.line",
        "move_id",
        string="Mostakhlas Details",
        copy=False,
    )

    def write(self, vals):
        if self.env.context.get("arka_mostakhlas_proforma"):
            vals = dict(vals)
            vals["move_type"] = "out_invoice"
        return super().write(vals)

    def _prepare_mostakhlas_detail_commands(self, mostakhlas_lines):
        commands = []
        for line in mostakhlas_lines:
            contract_total = (line.product_qty or 0.0) * (line.price_unit or 0.0)
            progress_percent = line.progress_percent or 0.0
            commands.append(Command.create({
                "sequence_int": line.sequence_int,
                "product_id": line.product_id.id,
                "name": line.name or line.product_id.display_name,
                "product_uom_id": line.product_uom.id,
                "product_qty": line.product_qty,
                "price_unit": line.price_unit,
                "discount": line.discount,
                "tax_ids": [Command.set(line.taxes_id.ids)],
                "contract_total": contract_total,
                "progress_percent": progress_percent,
                "executed_value": contract_total * (progress_percent / 100.0),
                "notes": line.name,
            }))
        return commands

    def _write_mostakhlas_snapshot(self, source_record, mostakhlas_lines, report_xmlid, number):
        self.ensure_one()
        report_pdf, _ = self.env["ir.actions.report"]._render_qweb_pdf(
            report_xmlid, [source_record.id]
        )
        first_line = mostakhlas_lines[:1]
        self.write({
            "is_mostakhlas_invoice": True,
            "mostakhlas_number": number,
            "mostakhlas_date": source_record.date_mostakhlas or fields.Date.context_today(source_record),
            "mostakhlas_type": first_line.mostakhlas_type_id.name if first_line else False,
            "mostakhlas_pdf_filename": f"{number or source_record.name}-mostakhlas.pdf",
            "mostakhlas_pdf": base64.b64encode(report_pdf),
            "mostakhlas_detail_line_ids": [
                Command.clear(),
                *self._prepare_mostakhlas_detail_commands(mostakhlas_lines),
            ],
        })


class AccountMoveMostakhlasLine(models.Model):
    _name = "account.move.mostakhlas.line"
    _description = "Account Move Mostakhlas Detail"
    _order = "sequence_int, id"

    move_id = fields.Many2one(
        "account.move",
        required=True,
        ondelete="cascade",
        index=True,
    )
    currency_id = fields.Many2one(
        related="move_id.currency_id",
        readonly=True,
    )
    sequence_int = fields.Integer(string="#")
    product_id = fields.Many2one("product.product", string="Product")
    name = fields.Text(string="Description")
    product_uom_id = fields.Many2one("uom.uom", string="UoM")
    product_qty = fields.Float(string="Contract Qty")
    price_unit = fields.Float(string="Unit Price")
    discount = fields.Float(string="Disc.%")
    tax_ids = fields.Many2many("account.tax", string="Taxes")
    contract_total = fields.Monetary(string="Contract Total")
    progress_percent = fields.Float(string="Current Progress %")
    executed_value = fields.Monetary(string="Executed Value")
    notes = fields.Text(string="Notes")
