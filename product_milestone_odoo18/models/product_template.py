from odoo import fields, models, api
from odoo.exceptions import UserError

# =========================================================
# ثابت Company Registry لشركة Arka
# =========================================================
ARKA_COMPANY_REGISTRY = "1010689416"
# =========================================================


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('is_milestone_flag')
    def _onchange_is_milestone_flag(self):
        for rec in self:
            # لو بيحاول يفعل الفلاج وفيه قيم في milestone_ids
            if rec.is_milestone_flag and rec.milestone_ids:
                rec.is_milestone_flag = False  # رجع الفلاج زي ما كان
                return {
                    'warning': {
                        'title': "تحذير",
                        'message': "يجب إزالة الـ Milestones من الحقل أولاً قبل تفعيل هذا الخيار.",
                    }
                }

    # ======================================================
    # هل الشركة الحالية = ARKA ؟
    # ======================================================
    is_arka_company = fields.Boolean(
        compute="_compute_is_arka_company",
        store=False
    )

    def _compute_is_arka_company(self):
        for rec in self:
            rec.is_arka_company = (
                rec.env.company.company_registry == ARKA_COMPANY_REGISTRY
            )

    # ======================================================
    # هل نظهر حقل milestones ؟
    # يظهر في كل الحالات ماعدا:
    # - لو type = milestone → يختفي
    # ======================================================
    show_milestone_field = fields.Boolean(
        compute='_compute_show_milestone_field',
        store=False
    )

    @api.depends('type', 'is_arka_company')
    def _compute_show_milestone_field(self):
        for rec in self:
            rec.show_milestone_field = (
                rec.is_arka_company and rec.type != 'milestone'
            )

    # ======================================================
    # إضافة نوع جديد Milestone — فقط في Arka
    # ======================================================

    # ======================================================
    # جلب شركة Arka
    # ======================================================
    def _get_arka_company(self):
        return self.env['res.company'].search(
            [('company_registry', '=', ARKA_COMPANY_REGISTRY)],
            limit=1
        )

    # ======================================================
    # NEW: لون لكل milestone
    # ======================================================
    color = fields.Integer("Color Index")

    # ======================================================
    # Many2many Milestones تبع Arka فقط
    # ======================================================
    milestone_ids = fields.Many2many(
        comodel_name='product.template',
        relation='product_milestone_rel',
        column1='product_id',
        column2='milestone_id',
        string='Milestones',
    )

    is_milestone_flag = fields.Boolean(
        string="Is Milestone (Flag)",
        help="Use this flag if you want the product to be treated as a milestone without changing its type."
    )

    # ======================================================
    # Create — Milestone فقط في Arka + set color
    # ======================================================
    @api.model
    def create(self, vals):
        is_milestone = vals.get('type') == 'milestone'

        if is_milestone:
            if self.env.company.company_registry != ARKA_COMPANY_REGISTRY:
                raise UserError("You can create Milestones only in ARKA company.")


        record = super().create(vals)

        # بعد إنشاء الـ milestone: نحدد لون ثابت
        if record.type == 'milestone':
            record.color = record.id % 12

        return record

    # ======================================================
    # Write — منع Milestone خارج Arka
    # ======================================================
    def write(self, vals):
        if vals.get('type') == 'milestone':
            if self.env.company.company_registry != ARKA_COMPANY_REGISTRY:
                raise UserError("Only ARKA company can convert products into Milestones.")

        res = super().write(vals)

        # تحديث اللون لو المنتج بقى milestone
        for rec in self:
            if rec.type == 'milestone' and not rec.color:
                rec.color = rec.id % 12

        return res
