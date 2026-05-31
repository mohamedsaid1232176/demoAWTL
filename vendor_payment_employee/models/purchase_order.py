from odoo import models, fields, _, api
from odoo.exceptions import UserError

ARKA_COMPANY_REGISTRY = "1010689416"

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    show_workflow = fields.Boolean(
        string="Show Workflow",
        compute='_compute_show_workflow',
        store=True
    )

    purchase_state = fields.Selection([('draft','Draft'),
                                       ('procurement_officer', 'Procurement Officer'),
                                        ('purchase_manager', 'Purchase Manager'),
                                        ('ceo_confirmed','CO Confirmed')],
                                        string='Purchase State',readonly=True ,default='draft',)

    @api.depends('company_id')
    def _compute_show_workflow(self):
        for order in self:
            order.show_workflow = (order.company_id.company_registry == '1010689416')



    def action_submit_request(self):
        """Draft → procurement_officer"""
        for order in self:
            if order.company_id.company_registry != '1010689416':
                order.message_post(body=_("This workflow is not applicable for this company."))
                continue

            po_procurement_officer = self.env.ref(
                'vendor_payment_employee.group_procurement_officer',
                raise_if_not_found=False
            )
            if not po_procurement_officer:
                continue

            order.write({'purchase_state': 'procurement_officer'})

            order.message_post(
                body=_("Purchase Order submitted to <b>Procurement Officer</b> by <b>%s</b>.") % self.env.user.name
            )

    def action_review(self):
        """procurement_officer → purchase_manager"""
        for order in self:
            if order.company_id.company_registry != '1010689416':
                order.message_post(body=_("This workflow is not applicable for this company."))
                continue

            po_purchase_manager = self.env.ref(
                'vendor_payment_employee.group_purchase_manager',
                raise_if_not_found=False
            )
            if not po_purchase_manager:
                continue

            order.write({'purchase_state': 'purchase_manager'})
            order.message_post(
                body=_("Purchase Order moved to <b>Purchase Manager</b> stage by %s.") % self.env.user.name
            )

    def action_ceo_confirm(self):
        """CO confirms the purchase order and triggers the real confirm logic"""
        for order in self:
            if order.company_id.company_registry != '1010689416':
                order.message_post(body=_("CO confirmation skipped: not applicable for this company."))
                continue

            # call original Odoo confirm
            order.button_confirm()

            order.write({
                'purchase_state': 'ceo_confirmed'
            })

            order.message_post(
                body=_("Purchase Order confirmed by CO <b>%s</b>.") % self.env.user.name,
            )

    def button_confirm(self):
        res = super().button_confirm()

        for order in self:
            if order.company_id.company_registry != ARKA_COMPANY_REGISTRY:
                continue

            pickings = order.picking_ids

            for picking in pickings:
                dest = picking.location_dest_id

                # if dest and dest.location_id:
                #     dest.location_id = False

        return res