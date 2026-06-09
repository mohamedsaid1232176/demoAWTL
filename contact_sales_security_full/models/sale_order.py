from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.osv import expression


# ==============================
# ✅ Sales Order Approval
# ==============================
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        if not self.env.user.can_confirm_sale:
            raise UserError("❌ You are not allowed to confirm this Sales Order.")
        return super().action_confirm()


# ==============================
# ✅ Users Fields (Contacts Access + Sale Approval)
# ==============================
class ResUsers(models.Model):
    _inherit = 'res.users'

    can_confirm_sale = fields.Boolean(string="Allow Confirm Sale Order")

    contact_access_level = fields.Selection([
        ('own', 'Own Contacts'),
        ('all', 'All Contacts'),
    ], string="Contacts Access", default='own')


# ==============================
# ✅ ResPartner — Contacts Visibility (Odoo 17)
# ==============================
class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _apply_own_contacts_domain(self, domain):
        """
        بيضيف فلتر 'own contacts' على الـ domain.
        بيتطبق بس لو الـ user مش superuser وعنده 'own' level.
        """
        user = self.env.user
        if not self.env.su and user.contact_access_level == 'own':
            domain = expression.AND([
                domain or [],
                [('user_id', '=', user.id)],
            ])
        return domain

    @api.model
    def web_search_read(self, domain=None, specification=None, offset=0,
                        limit=None, order=None, count_limit=None):
        """
        بيتشتغل بس لما الـ web client يعرض قائمة (Kanban / List).
        مش بيأثر على العمليات الداخلية في Odoo زي Users / Sales / إلخ.
        """
        domain = self._apply_own_contacts_domain(domain)
        return super().web_search_read(
            domain=domain,
            specification=specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit,
        )

    @api.model
    def search_count(self, domain, limit=None):
        """
        عشان الـ pagination يتحسب صح.
        """
        domain = self._apply_own_contacts_domain(domain)
        return super().search_count(domain, limit=limit)


# ==============================
# ✅ Res Config Settings (Recaptcha)
# ==============================
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    recaptcha_public_key = fields.Char(string="Recaptcha Public Key")
    recaptcha_private_key = fields.Char(string="Recaptcha Private Key")
    recaptcha_min_score = fields.Float(string="Recaptcha Minimum Score", default=0.5)