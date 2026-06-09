from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    technician_ids = fields.Many2many(
        'technician.technician',
        string="Technicians",
        required=True
    )

    vehicle_count = fields.Char(
        string="vehicle or plate number",
        required=True
    )

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals['vehicle_count'] = self.vehicle_count
        return vals




class AccountMove(models.Model):
    _inherit = 'account.move'

    vehicle_count = fields.Char(
        string="vehicle or plate number",
        readonly=True
    )
# =========================
# Sale Report
# =========================
class SaleReport(models.Model):
    _inherit = 'sale.report'

    customer_phone = fields.Char(string="Phone")
    vehicle_count = fields.Char(string="Vehicles")
    warehouse_custom_id = fields.Many2one('stock.warehouse', string="Warehouse")
    technician_names = fields.Char(string="Technicians")

    def _query(self):
        query = super()._query()

        query = query.replace(
            "SELECT",
            """
            SELECT
                MAX(partner.phone) as customer_phone,
                MAX(s.vehicle_count) as vehicle_count,
                CAST(MAX(s.warehouse_id) AS INTEGER) as warehouse_custom_id,

                (
                    SELECT STRING_AGG(t.name, '  -->  ')
                    FROM sale_order_technician_technician_rel rel
                    JOIN technician_technician t
                        ON t.id = rel.technician_technician_id
                    WHERE rel.sale_order_id = s.id
                ) as technician_names,
            """
        )

        return query

