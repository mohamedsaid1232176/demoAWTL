from odoo import models, api, fields
from odoo.exceptions import ValidationError
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    opportunity_id = fields.Many2one(
        'crm.lead',
        string="Pipeline / Opportunity",
        readonly=True,
    )

    is_milestone_quotation_generated = fields.Boolean(
        compute="_compute_is_milestone_quotation_generated",
        store=False
    )

    def _compute_is_milestone_quotation_generated(self):
        for rec in self:
            rec.is_milestone_quotation_generated = rec.opportunity_id.is_milestone_quotation_generated

    show_tabs_user = fields.Boolean(
        string="Show Tabs Based on User",
        compute="_compute_show_tabs_user"
    )

    def _compute_show_tabs_user(self):
        for rec in self:
            rec.show_tabs_user = rec.env.user.show_sale_tabs


class ResPartner(models.Model):
    _inherit = 'res.partner'

    total_all_due = fields.Float(string="Total All Due", compute='_compute_total_all_due')

    def _compute_total_all_due(self):
        for rec in self:
            rec.total_all_due = 0  # حط الحساب اللي انت عايزه

    has_moves = fields.Boolean(compute='_compute_has_moves')

    def _compute_has_moves(self):
        for rec in self:
            rec.has_moves = bool(rec.invoice_ids)


class ResUsers(models.Model):
    _inherit = "res.users"

    show_sale_tabs = fields.Boolean(
        string="Show Sale Tabs",
        default=False
    )

    can_see_all_records = fields.Boolean(string="Can See All Records")

    show_project_management_app = fields.Boolean(
        string="Show Projects Management App",
        compute="_compute_show_project_management_app",
        inverse="_inverse_show_project_management_app",
        store=False,
    )

    def _get_project_management_group(self):
        return self.env.ref("project_management_app.group_project_management_app", raise_if_not_found=False)

    def _compute_show_project_management_app(self):
        group = self._get_project_management_group()
        for user in self:
            user.show_project_management_app = bool(group and group in user.groups_id)

    def _inverse_show_project_management_app(self):
        group = self._get_project_management_group()
        if not group:
            return
        for user in self:
            if user.show_project_management_app:
                user.groups_id = [(4, group.id)]
            else:
                user.groups_id = [(3, group.id)]


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model_create_multi
    def create(self, vals_list):
        # لو الأكشن بتاعك هو اللي فتح الصفحة
        if self.env.context.get('hide_crm_buttons'):
            raise ValidationError("غير مسموح بإنشاء Leads في هذه الشاشة.")
        return super().create(vals_list)


    # make customer see All records in Crm
    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):

        # skip
        if self.env.context.get('skip_filter'):
            return super().read_group(domain, fields, groupby,
                                      offset=offset, limit=limit,
                                      orderby=orderby, lazy=lazy)

        user = self.env.user

        # لو يشوف الكل
        if user.can_see_all_records:
            return super().read_group(domain, fields, groupby,
                                      offset=offset, limit=limit,
                                      orderby=orderby, lazy=lazy)

        # فلتر
        my_domain = [('create_uid', '=', user.id)]

        domain = expression.AND([domain or [], my_domain])

        return super().read_group(domain, fields, groupby,
                                  offset=offset, limit=limit,
                                  orderby=orderby, lazy=lazy)
