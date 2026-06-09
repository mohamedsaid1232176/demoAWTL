# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleMostakhlasWizard(models.TransientModel):
    _name = "sale.mostakhlas.wizard"
    _description = "تأكيد طباعة مستخلص البيع"

    date_mostakhlas = fields.Date(
        string="تاريخ المستخلص",
        required=True,
    )

    def action_confirm(self):
        so = self.env["sale.order"].browse(
            self._context.get("active_id")
        )
        so.date_mostakhlas = self.date_mostakhlas
        action = so.action_print_sale_mostakhlas()
        action["close_on_report_download"] = True
        return action
