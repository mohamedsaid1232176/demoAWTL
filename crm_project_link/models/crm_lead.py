from odoo import models, fields, api
from odoo.exceptions import UserError

from odoo.exceptions import ValidationError

ARKA_COMPANY_REGISTRY = "311369490700003"


class ResUsers(models.Model):
    _inherit = "res.users"

    color_field = fields.Integer("Color Index")  # لإظهار اللون على الـ tags

    @api.model
    def create(self, vals):
        user = super().create(vals)
        if not user.color:
            user.color = user.id % 12
        return user

    def write(self, vals):
        res = super().write(vals)
        for user in self:
            if not user.color:
                user.color = user.id % 12
        return res


class CrmLead(models.Model):
    _inherit = "crm.lead"

    def init(self):
        self.pool.post_init(self._setup_kind_of_event_data)

    project_type = fields.Selection(
        [
            ('project', 'Project'),
        ],
        string="Operation Type",
        default='project'
    )
    #             ('lohat', 'اللوحات'),

    show_project_info = fields.Boolean(compute="_compute_show_project_info")
    show_product_field = fields.Boolean(compute="_compute_show_project_info")

    @api.depends("project_type")
    def _compute_show_project_info(self):
        for rec in self:
            rec.show_project_info = (rec.project_type == 'project')
            rec.show_product_field = (rec.project_type == 'final_product')

    # ---------------------------
    # Smart Button → Open BOMs
    # ---------------------------

    def action_open_bom(self):
        self.ensure_one()

        if not self.product_idd:
            raise UserError("من فضلك اختر المنتج أولاً قبل إنشاء Bill of Materials.")

        return {
            "type": "ir.actions.act_window",
            "name": "Create Bill of Materials",
            "res_model": "mrp.bom",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_product_tmpl_id": self.product_idd.product_tmpl_id.id,
            }
        }

    # ---------------------------
    # Product
    # ---------------------------

    product_idd = fields.Many2one(
        "product.product",
        string="Product",
    )

    # >>> added – does product have BOM?
    has_bom = fields.Boolean(compute="_compute_has_bom", store=False)

    @api.depends("product_idd")
    def _compute_has_bom(self):
        Bom = self.env["mrp.bom"]
        for rec in self:
            if not rec.product_idd:
                rec.has_bom = False
                continue

            product = rec.product_idd

            # لو المنتج ليه Variants
            if product.product_template_attribute_value_ids:
                bom = Bom._bom_find(product)
                rec.has_bom = bool(bom.get(product) if isinstance(bom, dict) else bom)
            else:
                # مفيش Variants → ندور على الـ template
                bom = Bom.search([("product_tmpl_id", "=", product.product_tmpl_id.id)], limit=1)
                rec.has_bom = bool(bom)

    # >>> added – has quotation?
    has_quotation = fields.Boolean(compute="_compute_has_quotation", store=False)

    def _compute_has_quotation(self):
        for rec in self:
            rec.has_quotation = bool(
                self.env["sale.order"].search_count([("opportunity_id", "=", rec.id)])
            )

    # >>> added – action to show existing BOM
    def action_show_bom(self):
        self.ensure_one()
        Bom = self.env["mrp.bom"]

        product = self.product_idd
        if not product:
            raise UserError("Please select a product first!")

        # 1) حاول تجيب الـ BOM بالـ variant
        bom_result = Bom._bom_find(product)

        # 2) لو رجع dict → خد الـ record
        if isinstance(bom_result, dict):
            bom = bom_result.get(product)
        else:
            bom = bom_result

        # 3) لو مفيش → دور على template
        if not bom:
            bom = Bom.search([("product_tmpl_id", "=", product.product_tmpl_id.id)], limit=1)

        # 4) لو برضه مفيش → Error
        if not bom:
            raise UserError("No Bill of Materials created for this product.")

        return {
            "type": "ir.actions.act_window",
            "name": "Bill of Materials",
            "res_model": "mrp.bom",
            "view_mode": "form",
            "res_id": bom.id,
        }

    unit_cost_bom = fields.Float(
        string="Unit Cost (BoM)",
        compute="_compute_unit_cost_bom",
        store=False
    )

    @api.depends('product_idd')
    def _compute_unit_cost_bom(self):
        Report = self.env['report.mrp.report_bom_structure']
        Warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1
        )
        Bom = self.env["mrp.bom"]

        for rec in self:
            rec.unit_cost_bom = 0.0

            if not rec.product_idd:
                continue

            product = rec.product_idd

            # 1) حاول تجيب BoM بالـ product variant
            bom_result = Bom._bom_find(product)

            # 2) لو رجع dict → خد الـ bom record
            if isinstance(bom_result, dict):
                bom = bom_result.get(product)
            else:
                bom = bom_result

            # 3) لو مفيش BoM للـ variant → دور على الـ Template
            if not bom:
                bom = Bom.search([("product_tmpl_id", "=", product.product_tmpl_id.id)], limit=1)

            # 4) لو ما زال مفيش BoM → سيبه
            if not bom:
                continue

            # 5) BoM Quantity
            bom_qty = bom.product_qty or 1.0

            # 6) احصل على نفس التكلفة اللي UI بيجيبها
            bom_data = Report._get_bom_data(
                bom,
                Warehouse,
                product=product,
                line_qty=bom_qty,
                level=0
            )

            rec.unit_cost_bom = bom_data.get('bom_cost', 0.0)

    product_qty = fields.Float(string="Quantity", default=1)

    # ---------------------------
    # Create quotation
    # ---------------------------
    margin = fields.Float(
        string="Margin (%)",
        default=0.0,
        help="Margin percentage added on top of BOM cost."
    )

    def action_create_quotation_from_lead(self):
        self.ensure_one()

        if not self.product_idd:
            raise UserError("Please select a Product first!")

        if not self.partner_id:
            raise UserError("Please select a Customer first!")

        bom = self._get_bom_for_product(self.product_idd)

        if not bom:
            raise UserError("No Bill of Materials found for this product.")

        qty = bom.product_qty or 1.0

        margin_ratio = (self.margin or 0.0) / 100.0
        unit_price = self.unit_cost_bom + (self.unit_cost_bom * margin_ratio)

        so = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'opportunity_id': self.id,
        })

        self.env['sale.order.line'].create({
            'order_id': so.id,
            'product_id': self.product_idd.id,
            'product_uom_qty': qty,
            'price_unit': unit_price / qty,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': so.id,
        }

    # ---------------------------
    # old ARKA code
    # ---------------------------

    date_start = fields.Date()
    date_end = fields.Date()
    project_id = fields.Many2one("project.project", string="Project",readonly=1)
    is_project_confirmed = fields.Boolean(default=False)

    won_text = fields.Char(
        string="Name Project",
        help="النص الذي يظهر عند تحويل الفرصة إلى Won."
    )
    is_won_stage = fields.Boolean(compute="_compute_is_won_stage")

    @api.depends("stage_id")
    def _compute_is_won_stage(self):
        for rec in self:
            rec.is_won_stage = bool(rec.stage_id and rec.stage_id.is_won)

    def action_set_won_rainbowman(self):
        won_stage = self.env['crm.stage'].search([('is_won', '=', True)], limit=1)

        for lead in self:
            # 1 — لو لسه ما أكدش
            if not lead.is_project_confirmed:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Confirm Project Creation',
                    'res_model': 'lead.won.confirm.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_lead_id': lead.id,
                        'default_new_stage_id': won_stage.id,
                    },
                }

    def write(self, vals):
        if vals.get("kind_of_event") and not vals.get("kind_of_event_ids"):
            kind_id = self._get_kind_of_event_id(vals["kind_of_event"])
            if kind_id:
                vals["kind_of_event_ids"] = [(4, kind_id)]

        res = super().write(vals)

        for lead in self:
            # إذا المرحلة Won → ممنوع تعديل won_text
            if lead.is_won_stage and "won_text" in vals:
                raise ValidationError("لا يمكن تعديل هذا الحقل بعد تحويل الفرصة إلى Won.")

            if lead.project_id:
                updates = {}

                if "date_start" in vals:
                    updates["date_start"] = lead.date_start

                if "date_end" in vals:
                    updates["date"] = lead.date_end

                if updates:
                    lead.project_id.write(updates)

        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("kind_of_event") and not vals.get("kind_of_event_ids"):
                kind_id = self._get_kind_of_event_id(vals["kind_of_event"])
                if kind_id:
                    vals["kind_of_event_ids"] = [(4, kind_id)]
        return super().create(vals_list)

    is_arka_company = fields.Boolean(
        compute="_compute_is_arka_company",
        store=False
    )

    def _compute_is_arka_company(self):
        for rec in self:
            rec.is_arka_company = (
                    rec.env.company.company_registry == ARKA_COMPANY_REGISTRY
            )

    project_manager_ids = fields.Many2many(
        "res.users",
        string="Project Managers",
    )

    @api.onchange("project_id")
    def _onchange_project_id_set_manager(self):
        if self.project_id:

            if self.project_id.user_id:
                self.project_manager_ids = [(6, 0, [self.project_id.user_id.id])]

            if self.project_id.date_start:
                self.date_start = self.project_id.date_start
            else:
                self.date_start = False

            if self.project_id.date:
                self.date_end = self.project_id.date
            else:
                self.date_end = False

    def _get_bom_for_product(self, product):
        Bom = self.env['mrp.bom']

        # اول محاولة: BOM للـ variant
        bom_result = Bom._bom_find(product)

        # لو dict → خد الـ record
        if isinstance(bom_result, dict):
            bom = bom_result.get(product)
        else:
            bom = bom_result

        # لو مفيش BOM للـ variant روح للـ template
        if not bom:
            bom = Bom.search([
                ('product_tmpl_id', '=', product.product_tmpl_id.id)
            ], limit=1)

        return bom

    project_event_type = fields.Selection(
        [
            ('bom', 'BOM'),
        ],
        string="Project Category",
        default='bom',
    )
    show_event_category = fields.Boolean(compute="_compute_show_project_info")

    @api.depends("project_type")
    def _compute_show_project_info(self):
        for rec in self:
            rec.show_project_info = (rec.project_type == 'project')
            rec.show_product_field = (rec.project_type == 'final_product')
            rec.show_event_category = (rec.project_type == 'project')

    # -------- Event Fields Tab  ----------
    event_location = fields.Char("Event Location")
    event_latitude = fields.Float("Latitude")
    event_longitude = fields.Float("Longitude")

    event_attendees = fields.Integer("Number of Attendees")

    event_has_gifts = fields.Selection(
        [
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        string="Are there gifts?"
    )
    kind_of_event = fields.Selection(
        [
            ('launching', 'التدشين'),
            ('internal_comments', 'الفعاليات الداخلية'),
        ],
        string="Legacy Kind of Event"
    )
    kind_of_event_id = fields.Many2one("kind.of.event", string="Legacy Kind of Event Record")
    kind_of_event_ids = fields.Many2many(
        "kind.of.event",
        "crm_lead_kind_of_event_rel",
        "lead_id",
        "kind_id",
        string="Kind of Event",
    )

    gift_count = fields.Integer("Number of Gifts")
    gift_item_ids = fields.Many2many("gift.type", string="Gift Types")

    event_type_id = fields.Many2one("event.type", string="Event Type")

    other_requests = fields.Text("customer Requests")

    def _get_kind_of_event_id(self, legacy_key):
        kind = self.env["kind.of.event"].search([("legacy_key", "=", legacy_key)], limit=1)
        return kind.id if kind else False

    def _setup_kind_of_event_data(self):
        self._create_default_kind_of_event_records()
        self._migrate_kind_of_event_selection()

    def _create_default_kind_of_event_records(self):
        KindOfEvent = self.env["kind.of.event"].sudo()
        for legacy_key, name in [
            ("launching", "التدشين"),
            ("internal_comments", "الفعاليات الداخلية"),
        ]:
            kind = KindOfEvent.search([("legacy_key", "=", legacy_key)], limit=1)
            if not kind:
                kind = KindOfEvent.search([("name", "=", name)], limit=1)
            if kind:
                if not kind.legacy_key:
                    kind.legacy_key = legacy_key
            else:
                KindOfEvent.create({
                    "name": name,
                    "legacy_key": legacy_key,
                })

    def _migrate_kind_of_event_selection(self):
        self.env.cr.execute("""
            INSERT INTO crm_lead_kind_of_event_rel (lead_id, kind_id)
            SELECT lead.id, kind.id
              FROM crm_lead lead
              JOIN kind_of_event kind ON lead.kind_of_event = kind.legacy_key
             WHERE lead.kind_of_event IS NOT NULL
               AND NOT EXISTS (
                    SELECT 1
                      FROM crm_lead_kind_of_event_rel rel
                     WHERE rel.lead_id = lead.id
                       AND rel.kind_id = kind.id
               )
        """)
        self.env.cr.execute("""
            INSERT INTO crm_lead_kind_of_event_rel (lead_id, kind_id)
            SELECT lead.id, lead.kind_of_event_id
              FROM crm_lead lead
             WHERE lead.kind_of_event_id IS NOT NULL
               AND NOT EXISTS (
                    SELECT 1
                      FROM crm_lead_kind_of_event_rel rel
                     WHERE rel.lead_id = lead.id
                       AND rel.kind_id = lead.kind_of_event_id
               )
        """)

    # -------- Visibility Fields ----------
    show_event_tab = fields.Boolean(compute="_compute_show_event_tab")
    show_gift_fields = fields.Boolean(compute="_compute_show_gift_fields")
    show_gift_tab = fields.Boolean(compute="_compute_show_gift_tab")
    show_both_tab = fields.Boolean(compute="_compute_show_location_tab")
    show_media_tab = fields.Boolean(compute="_compute_show_media_tab")
    media_type = fields.Html("Info")
    final_product_description = fields.Text("Boards Description")
    show_final_product_tab = fields.Boolean(compute="_compute_show_final_product_tab")

    # -------- Event Tab Visibility ----------
    @api.depends("project_type", "project_event_type")
    def _compute_show_event_tab(self):
        for rec in self:
            rec.show_event_tab = (
                    rec.project_type == 'project' and
                    rec.project_event_type == 'bom'
            )

    # -------- Gift Fields Visibility ----------
    @api.depends("event_has_gifts")
    def _compute_show_gift_fields(self):
        for rec in self:
            rec.show_gift_fields = (rec.event_has_gifts == 'yes')

    # -------- Gift Tab Visibility ----------
    @api.depends("project_type", "project_event_type")
    def _compute_show_gift_tab(self):
        for rec in self:
            rec.show_gift_tab = False

    @api.depends("project_type", "project_event_type")
    def _compute_show_location_tab(self):
        for rec in self:
            rec.show_both_tab = False

    @api.depends("project_type", "project_event_type")
    def _compute_show_media_tab(self):
        for rec in self:
            rec.show_media_tab = False

    @api.depends("project_type")
    def _compute_show_final_product_tab(self):
        for rec in self:
            rec.show_final_product_tab = (rec.project_type == "lohat")

    # ----------------------------
    # Final Product / Boards Fields
    # ----------------------------

    board_light_type = fields.Selection(
        [
            ('front', 'إضاءة أمامية'),
            ('back', 'إضاءة خلفية'),
        ],
        string="نوع الإضاءة المطلوبة"
    )

    acrylic_code = fields.Char("كود الأكريلك")
    acrylic_color = fields.Char("لون الأكريلك")

    light_code = fields.Char("كود الإضاءة")
    light_color = fields.Char("لون الإضاءة")
    light_type_detail = fields.Char("نوع الإضاءة")

    cladding_code = fields.Char("كود الكلادينج")
    cladding_color = fields.Char("لون الكلادينج")

    board_background = fields.Selection(
        [
            ('marble', 'رخام'),
            ('glass', 'زجاج'),
            ('cladding', 'كلادينج'),
            ('stone', 'حجر'),
            ('gypsum', 'جبس بورد'),
            ('cement', 'جدار أسمنت'),
        ],
        string="خلفية اللوحة"
    )

    board_height = fields.Float("ارتفاع اللوحة من الأرض")
    board_size = fields.Char("مقاس واجهة التركيب")

    board_attachment_image = fields.Binary("صورة واجهة المحل")
