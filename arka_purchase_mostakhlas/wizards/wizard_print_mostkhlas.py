from odoo import models, fields, api

class MostakhlasWizard(models.TransientModel):
    _name = "mostakhlas.wizard"
    _description = "Mostakhlas Confirmation Wizard"

    date_mostakhlas = fields.Date(
        string="Mostakhlas Date",
        required=True
    )

    def action_confirm(self):
        po = self.env["purchase.order"].browse(self._context.get("active_id"))

        # Save date
        po.date_mostakhlas = self.date_mostakhlas

        # Get report action
        action = po.action_print_mostakhlas()

        # Inject close wizard flag
        action["close_on_report_download"] = True

        return action
