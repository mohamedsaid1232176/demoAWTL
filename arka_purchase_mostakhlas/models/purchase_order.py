from odoo import models, fields, api
from odoo.exceptions import ValidationError

ARKA_COMPANY_REGISTRY = "311369490700003"


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # =========================
    #       SEQUENCE
    # =========================
    sequence = fields.Char(
        string="Sequence",
        readonly=True,
        copy=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if not order.sequence:
                order.sequence = "MO-0"
        return orders

    def _post_report_hook(self):
        # ده اللي هيرجع القيمة 0 بعد الطباعة
        self.vendor_payment_total_paid_in_mostkhlas = 0

    def action_print_mostakhlas(self):

        # رقم المستخلص
        if self.sequence:
            try:
                num = int(self.sequence.replace("MO-", ""))
                num += 1
            except Exception:
                num = 1
        else:
            num = 1

        self.sequence = f"MO-{num}"

        # =====================================================
        # 1. lines المعلمة فقط
        # =====================================================
        selected_lines = self.mostakhlas_line_ids.filtered(lambda l: l.print_in_report)

        # لو مفيش متعلم → اعتبرها error
        if not selected_lines:
            raise ValidationError("من فضلك اختر على الأقل بند واحد للطباعة.")

        # =====================================================
        # 2. تحديث نسبة الإنجاز (قبل مسح الـ checkboxes)
        # =====================================================
        for line in selected_lines:
            current = line.done_progress or 0.0
            new = current + (line.progress_percent or 0.0)

            # progress must be > 0
            if (line.progress_percent or 0.0) <= 0:
                raise ValidationError(
                    f"نسبة الإنجاز للسطر {line.sequence_int} يجب أن تكون أكبر من 0."
                )

            # total must not exceed 100%
            if new > 100:
                raise ValidationError(
                    f"إجمالي نسبة الإنجاز للسطر رقم {line.sequence_int} "
                    f"تخطت الحد المسموح به (100%)."
                )

            # Update
            line.done_progress = new

        # =====================================================
        # 3. نظّف buffer وسجل المختار فقط
        # =====================================================
        self.env["mostakhlas.print.buffer"].search([("order_id", "=", self.id)]).unlink()

        for line in selected_lines:
            self.env["mostakhlas.print.buffer"].create({
                "order_id": self.id,
                "line_id": line.id
            })

        # =====================================================
        # 4. اطبع التقرير (وما ترجّعش checkboxes لسه)
        # =====================================================
        action = self.env.ref(
            "arka_purchase_mostakhlas.action_report_mostakhlas"
        ).report_action(self)

        # =====================================================
        # 5. بعد الطباعة فقط → رجّع الفلاج False
        # =====================================================
        selected_lines.write({"print_in_report": False})

        # ====================================================
        #              Vendor Payments Logic
        # ====================================================

        # 1) كل الدفعات المدفوعة
        paid_payments = self.payment_ids.filtered(lambda p: p.state == 'paid')

        # 2) هات الدفعات اللي لسه ما اتستخدمتش
        new_payments = paid_payments.filtered(lambda p: not p.is_used_in_mostakhlas)

        # 4) vendor_payment_total = مجموع الدفعات الجديدة فقط

        # 3) لو أول طباعة → استخدم كل المدفوعات paid
        previously_used = self.payment_ids.filtered(lambda p: p.is_used_in_mostakhlas)

        if not previously_used:
            new_payments = paid_payments

        # 5) بعد الطباعة → علّم إنهم "اُستخدموا"
        # Disable duplicate compute during write
        new_payments.with_context(skip_duplicate_check=True).write({
            "is_used_in_mostakhlas": True
        })
        self.write({"vendor_payment_total_paid_in_mostkhlas": 0})

        return action

    # =========================
    #        FLAGS
    # =========================
    show_mostakhlas_tab = fields.Boolean(default=False)

    is_arka_company = fields.Boolean(
        compute="_compute_is_arka_company",
        store=False
    )

    @api.depends("company_id")
    def _compute_is_arka_company(self):
        for rec in self:
            rec.is_arka_company = bool(
                rec.company_id
                and rec.company_id.company_registry == ARKA_COMPANY_REGISTRY
            )

    # =========================
    #       RELATIONS
    # =========================
    mostakhlas_line_ids = fields.One2many(
        "purchase.mostakhlas.line",
        "order_id",
        string="Mostakhlas Lines"
    )

    payment_ids = fields.Many2many(
        "account.payment",
        string="Paid Payments",
        domain="""
          [
              ('state','=','paid'),
              ('partner_type','=','supplier'),
              ('payment_type','=','outbound'),
              ('partner_id','=',partner_id)
          ]
          """
    )

    project_id = fields.Many2one("project.project")

    # =========================
    #       TOTALS
    # =========================
    mostakhlas_untaxed = fields.Monetary(
        string="Untaxed Amount",
        compute="_compute_mostakhlas_totals",
        store=True
    )

    progress_percent = fields.Float(
        string="نسبة الإنجاز (%)",
        default=0.0
    )

    mostakhlas_tax = fields.Monetary(
        string="VAT Taxes",
        compute="_compute_mostakhlas_totals",
        store=True
    )

    mostakhlas_total = fields.Monetary(
        string="Total",
        compute="_compute_mostakhlas_totals",
        store=True
    )

    executed_contract_value = fields.Monetary(
        string="إجمالي قيمة الأعمال التعاقدية المنفذة",
        compute="_compute_mostakhlas_total",
        store=True,
        currency_field="currency_id"
    )

    executed_contract_value_vat = fields.Monetary(
        string="إجمالي قيمة الأعمال التعاقدية المنفذة شامل ضريبة القيمة المضافة",
        compute="_compute_mostakhlas_total",
        store=True,
        currency_field="currency_id"
    )

    vendor_payment_total = fields.Monetary(
        string="إجمالي دفعات المورد",
        compute="_compute_vendor_payment_total",
        currency_field="currency_id",
        store=True
    )

    vendor_payment_total_paid = fields.Monetary(
        string=" إجمالي دفعات المورد التي تم دفعها",
        compute="_compute_vendor_payment_total_paid",
        currency_field="currency_id",
        store=True
    )

    vendor_payment_total_paid_in_mostkhlas = fields.Monetary(
        string=" إجمالي دفعات المورد التي ستدفع في هذا المستخلص",
        compute="_compute_vendor_payment_total_paid_in_mostkhlas",
        currency_field="currency_id",
        store=True
    )

    vendor_payment_total_paid_in_mostkhlas_helper = fields.Monetary(
        compute="_compute_vendor_payment_total_paid_in_mostkhlas_helper",
        currency_field="currency_id",
        store=True
    )

    currency_id = fields.Many2one(
        related="company_id.currency_id",
        readonly=True
    )

    vendor_payment_total_all = fields.Monetary(
        string="إجمالي دفعات المورد",
        compute="_compute_vendor_payment_total_all",
        currency_field="currency_id",
        store=True
    )

    @api.depends("payment_ids.amount", "payment_ids.state")
    def _compute_vendor_payment_total_all(self):
        for order in self:
            payments = order.payment_ids.filtered(lambda p: p.state == "paid")
            order.vendor_payment_total_all = sum(payments.mapped("amount"))
    # =========================
    #     TOTALS COMPUTES
    # =========================

    @api.depends(
        "mostakhlas_line_ids.price_subtotal",
        "mostakhlas_line_ids.taxes_id",
        "mostakhlas_line_ids.product_qty",
        "mostakhlas_line_ids.price_unit",
    )
    def _compute_mostakhlas_totals(self):
        for order in self:
            untaxed = 0.0
            tax = 0.0

            # =========================================
            # ✅ استخدم buffer (نفس التقرير)
            # =========================================
            buffer_lines = self.env["mostakhlas.print.buffer"].search([
                ("order_id", "=", order.id)
            ]).mapped("line_id")

            # لو مفيش buffer → fallback لكل السطور
            if not buffer_lines:
                buffer_lines = order.mostakhlas_line_ids

            # =========================================
            # ✅ الحساب
            # =========================================
            for line in buffer_lines:
                untaxed += line.price_subtotal

                if line.taxes_id:
                    taxes_res = line.taxes_id.compute_all(
                        line.price_unit,
                        currency=order.currency_id,
                        quantity=line.product_qty,
                        product=line.product_id,
                        partner=order.partner_id,
                    )
                    tax += sum(t["amount"] for t in taxes_res["taxes"])

            # =========================================
            # ✅ النتائج
            # =========================================
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
    def _compute_mostakhlas_total(self):
        for order in self:
            untaxed = 0.0
            tax = 0.0
            executed_untaxed = 0.0
            executed_total = 0.0

            # =========================================
            # ✅ استخدم buffer (نفس التقرير)
            # =========================================
            buffer_lines = self.env["mostakhlas.print.buffer"].search([
                ("order_id", "=", order.id)
            ]).mapped("line_id")

            # لو مفيش buffer → fallback لكل السطور
            if not buffer_lines:
                buffer_lines = order.mostakhlas_line_ids

            # =========================================
            # ✅ الحساب
            # =========================================
            for line in buffer_lines:
                qty = line.product_qty or 0.0
                price = line.price_unit or 0.0

                line_untaxed = qty * price
                untaxed += line_untaxed

                # ✅ cumulative (Previous + Current)
                total_progress = (line.done_progress or 0.0) / 100.0
                executed_line_value = line_untaxed * total_progress

                executed_untaxed += executed_line_value

                if line.taxes_id:
                    taxes_res = line.taxes_id.compute_all(
                        price,
                        currency=order.currency_id,
                        quantity=qty,
                        product=line.product_id,
                        partner=order.partner_id,
                    )
                    tax_line = sum(t["amount"] for t in taxes_res["taxes"])
                    tax += tax_line

                    # ✅ VAT على القيمة المنفذة (التراكمية)
                    executed_total += executed_line_value * 1.15
                else:
                    executed_total += executed_line_value

            # =========================================
            # ✅ النتائج
            # =========================================
            order.mostakhlas_untaxed = untaxed
            order.mostakhlas_tax = tax
            order.mostakhlas_total = untaxed + tax

            order.executed_contract_value = executed_untaxed
            order.executed_contract_value_vat = executed_total
    # =========================
    #     PAYMENT TOTAL
    # =========================

    # field vendor_payment_total
    @api.depends("payment_ids.amount", "payment_ids.state")
    def _compute_vendor_payment_total(self):
        for order in self:
            payments = order.payment_ids.filtered(
                lambda p: p.state not in ("cancel",)
            )
            order.vendor_payment_total = sum(payments.mapped("amount"))

    @api.constrains("payment_ids", "payment_ids.amount", "mostakhlas_untaxed")
    def _check_vendor_payments_amount(self):
        for order in self:
            total_paid = sum(order.payment_ids.mapped("amount"))
            limit = order.mostakhlas_untaxed or 0.0

            if total_paid > limit:
                raise ValidationError(
                    f"إجمالي مبالغ دفعات المورد ({total_paid}) "
                    f"لا يجوز أن يتجاوز قيمة المستخلص  ({limit})."
                )

    # field vendor_payment_total_paid

    @api.depends("payment_ids.amount", "payment_ids.state")
    def _compute_vendor_payment_total_paid(self):
        for order in self:
            paid_payments = order.payment_ids.filtered(lambda p: p.state == "paid")
            order.vendor_payment_total_paid = sum(paid_payments.mapped("amount"))

    @api.constrains("payment_ids", "payment_ids.amount", "mostakhlas_untaxed")
    def _check_vendor_payments_amount_paid(self):
        for order in self:
            paid_payments = order.payment_ids.filtered(lambda p: p.state == "paid")
            total_paid = sum(paid_payments.mapped("amount"))
            limit = order.mostakhlas_untaxed or 0.0

            if total_paid > limit:
                raise ValidationError(
                    f"إجمالي مبالغ دفعات المورد ({total_paid}) "
                    f"لا يجوز أن يتجاوز قيمة المستخلص ({limit})."
                )

    # field vendor_payment_total_paid_in_mostkhlas
    @api.depends("payment_ids.amount", "payment_ids.state")
    def _compute_vendor_payment_total_paid_in_mostkhlas(self):
        for order in self:
            payments = order.payment_ids.filtered(
                lambda p: p.state == "paid" and not p.is_used_in_mostakhlas
            )
            order.vendor_payment_total_paid_in_mostkhlas = sum(payments.mapped("amount"))

    @api.constrains("payment_ids", "payment_ids.amount", "mostakhlas_untaxed", "payment_ids.state")
    def _check_vendor_payment_total_paid_in_mostkhlas(self):
        for order in self:
            total_paid = sum(order.payment_ids.mapped("amount"))
            limit = order.mostakhlas_untaxed or 0.0

            if total_paid > limit:
                raise ValidationError(
                    f"إجمالي مبالغ دفعات المورد ({total_paid}) "
                    f"لا يجوز أن يتجاوز قيمة المستخلص  ({limit})."
                )

    # field vendor_payment_total_paid_in_mostkhlas_helper
    @api.depends("payment_ids.amount", "payment_ids.state")
    def _compute_vendor_payment_total_paid_in_mostkhlas_helper(self):
        for order in self:
            payments = order.payment_ids.filtered(
                lambda p: p.state == "paid" and not p.is_used_in_mostakhlas
            )
            order.vendor_payment_total_paid_in_mostkhlas_helper = sum(payments.mapped("amount"))

    @api.constrains("payment_ids", "payment_ids.amount", "mostakhlas_untaxed", "payment_ids.state")
    def _check_vendor_payment_total_paid_in_mostkhlas_helper(self):
        for order in self:
            total_paid = sum(order.payment_ids.mapped("amount"))
            limit = order.mostakhlas_untaxed or 0.0

            if total_paid > limit:
                raise ValidationError(
                    f"إجمالي مبالغ دفعات المورد ({total_paid}) "
                    f"لا يجوز أن يتجاوز قيمة المستخلص  ({limit})."
                )

    # =========================
    #    OTHER INFO FIELDS
    # =========================
    project_manager = fields.Char(
        string="Project Manager",
        compute="_compute_project_manager",
        store=True
    )

    @api.depends("project_id", "project_id.user_id")
    def _compute_project_manager(self):
        for rec in self:
            if rec.project_id and rec.project_id.user_id:
                rec.project_manager = rec.project_id.user_id.name
            else:
                rec.project_manager = False

    technical_office_manager = fields.Char(string="Technical Office Manager")
    operations_manager = fields.Char(
        string="Operations Manager",
        default="مصطفى شاهين",
        readonly=True
    )
    subcontractor_name = fields.Char(
        string="Subcontractor Name",
        compute="_compute_subcontractor_name",
        store=True,
        readonly=True
    )

    @api.depends("partner_id")
    def _compute_subcontractor_name(self):
        for rec in self:
            rec.subcontractor_name = rec.partner_id.name if rec.partner_id else False

    date_subcontractor = fields.Date(string="Date")
    date_mostakhlas = fields.Date(string="التاريخ")

    # =========================
    #     MOSTAKHLAS TAB
    # =========================
    def action_open_mostakhlas_tab(self):
        for order in self:
            existing_products = set(order.mostakhlas_line_ids.mapped("product_id").ids)
            new_lines_vals = []

            # احسب آخر تسلسل موجود
            seq = len(order.mostakhlas_line_ids)

            for line in order.order_line.filtered(lambda l: not l.display_type):

                if line.product_id.id in existing_products:
                    continue

                seq += 1  # ← ← ← زيادة التسلسل لكل سطر جديد

                new_lines_vals.append({
                    "order_id": order.id,
                    "sequence_int": seq,  # ← ← ← تسلسل صحيح
                    "product_id": line.product_id.id,
                    "name": line.name,
                    "date_planned": line.date_planned,
                    "product_qty": line.product_qty,
                    "product_uom": line.product_uom.id,
                    "price_unit": line.price_unit,
                    "discount": line.discount,
                    "taxes_id": [(6, 0, line.taxes_id.ids)],
                    "analytic_distribution": line.analytic_distribution,
                })

            if new_lines_vals:
                self.env["purchase.mostakhlas.line"].create(new_lines_vals)

            order.show_mostakhlas_tab = True

        return True

    selected_mostakhlas_lines = fields.One2many(
        "purchase.mostakhlas.line",
        compute="_compute_selected_mostakhlas_lines",
        string="Selected Lines",
        store=False
    )

    @api.depends("mostakhlas_line_ids.print_in_report")
    def _compute_selected_mostakhlas_lines(self):
        for order in self:
            order.selected_mostakhlas_lines = order.mostakhlas_line_ids.filtered(
                lambda l: l.print_in_report
            )

    # دالة الـ Wizard
    def action_open_mostakhlas_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "mostakhlas.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_id": self.id},
        }


# =====================================================
#                  ACCOUNT PAYMENT
# =====================================================
class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _compute_duplicate_payment_ids(self):
        # لما يكون الفلاج موجود → ما تنفّذش الدوبليكيشن
        if self.env.context.get("skip_duplicate_check"):
            for rec in self:
                rec.duplicate_payment_ids = False
            return

        # otherwise → نفّذ الطبيعي
        return super()._compute_duplicate_payment_ids()

    purchase_order_id = fields.Many2one(
        "purchase.order",
        string="Purchase Order",
        ondelete="set null",
        index=True
    )
    # Checkbox → هل تم استخدام الدفع في مستخلص سابق؟
    is_used_in_mostakhlas = fields.Boolean(
        string="Is Used In Other Mostakhlas",
        default=False,
        readonly=True
    )

    employee_id = fields.Many2one("hr.employee", required=False)

    @api.onchange("purchase_order_id")
    def _onchange_purchase_order_id(self):
        if len(self) != 1:
            return

        if self.purchase_order_id:
            self.partner_id = self.purchase_order_id.partner_id
            self.partner_type = "supplier"
            self.payment_type = "outbound"


# =====================================================
#                     RES USERS
# =====================================================
class ResUsers(models.Model):
    _inherit = "res.users"

    def _update_arka_group_by_allowed_companies(self):
        group = self.env.ref("arka_purchase_mostakhlas.group_arka_company_only")

        for user in self:

            if user.has_group("base.group_system"):
                user.groups_id = [(4, group.id)]
                continue

            has_arka = any(
                company.company_registry == ARKA_COMPANY_REGISTRY
                for company in user.company_ids
            )

            if has_arka:
                if group not in user.groups_id:
                    user.groups_id = [(4, group.id)]
            else:
                if group in user.groups_id:
                    user.groups_id = [(3, group.id)]

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._update_arka_group_by_allowed_companies()
        return users

    def write(self, vals):
        res = super().write(vals)
        if "company_ids" in vals or "company_id" in vals:
            self._update_arka_group_by_allowed_companies()
        return res
