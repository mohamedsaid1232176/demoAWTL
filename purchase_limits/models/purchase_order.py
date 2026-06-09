from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # ==========================
    # Stage جديدة مستقلة
    # ==========================
    approval_stage = fields.Selection([
        ('none', 'موظف المشتريات '),
        ('waiting_purchase_manager', 'موافقة مدير المشتريات'),
        ('waiting_finance_manager', 'موافقة المدير المالي'),
        ('approved', 'اعتماد نهائي'),
    ], default='none', string="Approval Stage", tracking=True)

    # حقول إظهار الأزرار
    can_send_to_manager = fields.Boolean(compute="_compute_visibility")
    can_send_to_finance = fields.Boolean(compute="_compute_visibility")
    can_manager_confirm = fields.Boolean(compute="_compute_visibility")
    can_finance_confirm = fields.Boolean(compute="_compute_visibility")

    # ==========================
    # انتقالات المرحلة
    # ==========================
    def action_send_to_purchase_manager(self):
        self.approval_stage = "waiting_purchase_manager"
        # self._create_approval_activity("waiting_purchase_manager")  # ⛔ COMMENTED

    def action_send_to_finance_manager(self):
        self.approval_stage = "waiting_finance_manager"
        # self._create_approval_activity("waiting_finance_manager")  # ⛔ COMMENTED

    def action_approve_final(self):
        self.approval_stage = "approved"

    # ==========================
    # Confirm default logic
    # ==========================
    def button_confirm(self):
        user = self.env.user
        total = self.amount_total

        # ==========================================================
        # 1) المدير المالي أعلى صلاحية
        # ==========================================================
        if user.has_group("account.group_account_manager"):
            result = super().button_confirm()
            # self._create_inventory_activity()  # ⛔ COMMENTED
            self.approval_stage = "approved"
            return result

        # ==========================================================
        # 2) مدير مشتريات
        # ==========================================================
        if user.has_group("purchase.group_purchase_manager"):

            # حالة none
            if self.approval_stage == 'none':
                if total <= user.purchase_manager_to:
                    result = super().button_confirm()
                    # self._create_inventory_activity()  # ⛔ COMMENTED
                    self.approval_stage = "approved"
                    return result
                else:
                    raise UserError("المبلغ خارج صلاحياتك. برجاء تحويل الطلب للمدير المالي.")

            # حالة waiting_purchase_manager
            if self.approval_stage == 'waiting_purchase_manager':
                if user.purchase_manager_from <= total <= user.purchase_manager_to:
                    result = super().button_confirm()
                    # self._create_inventory_activity()  # ⛔ COMMENTED
                    self.approval_stage = "approved"
                    return result
                else:
                    raise UserError("المبلغ خارج صلاحياتك. برجاء تحويل الطلب للمدير المالي.")

            raise UserError("ليست لديك صلاحية للتأكيد في هذه المرحلة.")

        # ==========================================================
        # 3) موظف مشتريات
        # ==========================================================
        if user.has_group("purchase.group_purchase_user"):

            if self.approval_stage == 'none':
                if total <= user.purchase_user_limit:
                    result = super().button_confirm()
                    # self._create_inventory_activity()  # ⛔ COMMENTED
                    self.approval_stage = "approved"
                    return result
                else:
                    raise UserError("المبلغ أكبر من صلاحياتك. برجاء تحويل الطلب لمدير المشتريات.")
            else:
                raise UserError("ليست لديك صلاحية للتأكيد في هذه المرحلة.")

        # ==========================================================
        # 4) أي مستخدم آخر
        # ==========================================================
        raise UserError("ليست لديك صلاحية للتأكيد في هذه المرحلة.")

    # ==========================
    # Button visibility logic
    # ==========================
    @api.depends("amount_total", "approval_stage")
    def _compute_visibility(self):
        for rec in self:
            user = rec.env.user
            total = rec.amount_total

            rec.can_send_to_manager = False
            rec.can_send_to_finance = False
            rec.can_manager_confirm = False
            rec.can_finance_confirm = False

            # ======================
            # 1) المدير المالي
            # ======================
            if user.has_group("account.group_account_manager"):
                if rec.approval_stage == 'waiting_finance_manager':
                    rec.can_finance_confirm = True
                continue

            # ======================
            # 2) مدير مشتريات (Administrator)
            # ======================
            if user.has_group("purchase.group_purchase_manager"):

                # مرحلة none → logic القفز للمالية
                if rec.approval_stage == 'none':
                    if total > user.purchase_manager_to:
                        rec.can_send_to_finance = True
                    elif user.purchase_manager_from <= total <= user.purchase_manager_to:
                        rec.can_manager_confirm = True
                    continue

                # مرحلة انتظار مدير المشتريات
                if rec.approval_stage == 'waiting_purchase_manager':
                    if user.purchase_manager_from <= total <= user.purchase_manager_to:
                        rec.can_manager_confirm = True
                    elif total > user.purchase_manager_to:
                        rec.can_send_to_finance = True
                continue

            # ======================
            # 3) موظف مشتريات
            # ======================
            if user.has_group("purchase.group_purchase_user"):
                if rec.approval_stage == 'none' and total > user.purchase_user_limit:
                    rec.can_send_to_manager = True
                continue

    # ==========================
    # Create Activities based on Stage
    # ==========================
    def _create_approval_activity(self, stage):

        # 🔥🔥🔥 COMMENTED WHOLE METHOD CONTENT BELOW 🔥🔥🔥

        """
        Activity = self.env['mail.activity']
        Users = self.env['res.users']
        _logger = self.env['ir.logging']

        if stage == "waiting_purchase_manager":
            target_users = Users.search([
                ('groups_id', 'in', self.env.ref('purchase.group_purchase_manager').id)
            ])
            summary = "مطلوب موافقة مدير المشتريات"
            note = f"يرجى مراجعة أمر الشراء رقم {self.name}."

        elif stage == "waiting_finance_manager":
            target_users = Users.search([
                ('groups_id', 'in', self.env.ref('account.group_account_manager').id)
            ])
            summary = "مطلوب موافقة المدير المالي"
            note = f"يرجى مراجعة أمر الشراء رقم {self.name}."

        else:
            return

        self.message_post(body=f"🔔 بدء إنشاء Activities للمرحلة: {stage}")

        for user in target_users:
            Activity.create({
                'res_id': self.id,
                'res_model_id': self.env.ref('purchase.model_purchase_order').id,
                'user_id': user.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': summary,
                'note': note,
            })

            _logger.create({
                'name': 'Purchase Approval Activity',
                'type': 'server',
                'dbname': self._cr.dbname,
                'level': 'INFO',
                'message': f"Activity created for user: {user.name}",
                'path': 'purchase_order',
                'func': '_create_approval_activity',
                'line': '0',
            })

            self.message_post(body=f"✔ تم إرسال Activity إلى: <b>{user.name}</b>")

        if not target_users:
            self.message_post(body="⚠ لا يوجد مستخدمين مناسبين لهذه المرحلة!")
        """

    # ==========================
    # Create Inventory Activities on Confirm
    # ==========================
    def _create_inventory_activity(self):

        # 🔥🔥🔥 COMMENTED WHOLE METHOD CONTENT BELOW 🔥🔥🔥

        """
        Activity = self.env['mail.activity']
        Users = self.env['res.users']

        inventory_users = Users.search([
            ('groups_id', 'in', [
                self.env.ref('stock.group_stock_user').id,
                self.env.ref('stock.group_stock_manager').id
            ])
        ])

        summary = "تنبيه لإدارة المخازن"
        note = f"تم تأكيد أمر الشراء رقم {self.name}. يرجى بدء إجراءات الاستلام."

        self.message_post(body="📦 بدء إرسال Activities للمخازن.")

        for user in inventory_users:
            Activity.create({
                'res_id': self.id,
                'res_model_id': self.env.ref('purchase.model_purchase_order').id,
                'user_id': user.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': summary,
                'note': note,
            })

            _logger.info(f"[INVENTORY ACTIVITY] Created for {user.name}")

            self.message_post(body=f"✔ تم إرسال Activity لمستخدم المخازن: <b>{user.name}</b>")

        if not inventory_users:
            self.message_post(body="⚠ لا يوجد مستخدمين في قسم المخازن!")
        """



class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        result = super().button_validate()

        for picking in self:
            # picking._create_accounting_activity()  # ⛔ COMMENTED
            pass

        return result

    def _create_accounting_activity(self):

        # 🔥🔥🔥 COMMENTED WHOLE METHOD CONTENT BELOW 🔥🔥🔥

        """
        Activity = self.env['mail.activity']
        Users = self.env['res.users']

        accounting_groups = [
            'account.group_account_readonly',
            'account.group_account_invoice',
            'account.group_account_user',
            'account.group_account_manager',
        ]

        group_ids = []
        for g in accounting_groups:
            try:
                group_ids.append(self.env.ref(g).id)
            except:
                _logger.warning(f"[WARNING] Group not found: {g}")

        target_users = Users.search([('groups_id', 'in', group_ids)])

        summary = "حركة مخزون جديدة تم اعتمادها"
        note = f"تم عمل Validate للحركة: {self.name}. يرجى المتابعة من قسم الحسابات."

        self.message_post(body="📦 تم عمل Validate للحركة، وإرسال Activities للمحاسبين.")

        for user in target_users:
            Activity.create({
                'res_id': self.id,
                'res_model_id': self.env.ref('stock.model_stock_picking').id,
                'user_id': user.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': summary,
                'note': note,
            })

            _logger.info(f"[ACCOUNTING ACTIVITY] Created for accounting user: {user.name}")

            self.message_post(
                body=f"✔ تم إرسال Activity لمستخدم الحسابات: <b>{user.name}</b>"
            )

        if not target_users:
            self.message_post(body="⚠ لا يوجد مستخدمين في قسم المحاسبة!")
        """














































# from odoo import models, fields, api
# from odoo.exceptions import UserError
# import logging
#
# _logger = logging.getLogger(__name__)
#
#
# class PurchaseOrder(models.Model):
#     _inherit = "purchase.order"
#
#     # ==========================
#     # Stage جديدة مستقلة
#     # ==========================
#     approval_stage = fields.Selection([
#         ('none', 'موظف المشتريات '),
#         ('waiting_purchase_manager', 'موافقة مدير المشتريات'),
#         ('waiting_finance_manager', 'موافقة المدير المالي'),
#         ('approved', 'اعتماد نهائي'),
#     ], default='none', string="Approval Stage", tracking=True)
#
#     # حقول إظهار الأزرار
#     can_send_to_manager = fields.Boolean(compute="_compute_visibility")
#     can_send_to_finance = fields.Boolean(compute="_compute_visibility")
#     can_manager_confirm = fields.Boolean(compute="_compute_visibility")
#     can_finance_confirm = fields.Boolean(compute="_compute_visibility")
#
#     # ==========================
#     # انتقالات المرحلة
#     # ==========================
#     def action_send_to_purchase_manager(self):
#         self.approval_stage = "waiting_purchase_manager"
#         self._create_approval_activity("waiting_purchase_manager")
#
#     def action_send_to_finance_manager(self):
#         self.approval_stage = "waiting_finance_manager"
#         self._create_approval_activity("waiting_finance_manager")
#
#     def action_approve_final(self):
#         self.approval_stage = "approved"
#
#     # ==========================
#     # Confirm default logic
#     # ==========================
#     def button_confirm(self):
#         user = self.env.user
#         total = self.amount_total
#
#         # ==========================================================
#         # 1) المدير المالي أعلى صلاحية
#         # ==========================================================
#         if user.has_group("account.group_account_manager"):
#             result = super().button_confirm()
#             self._create_inventory_activity()
#             self.approval_stage = "approved"
#             return result
#
#         # ==========================================================
#         # 2) مدير مشتريات
#         # ==========================================================
#         if user.has_group("purchase.group_purchase_manager"):
#
#             # حالة none
#             if self.approval_stage == 'none':
#                 if total <= user.purchase_manager_to:
#                     result = super().button_confirm()
#                     self._create_inventory_activity()
#                     self.approval_stage = "approved"
#                     return result
#                 else:
#                     raise UserError("المبلغ خارج صلاحياتك. برجاء تحويل الطلب للمدير المالي.")
#
#             # حالة waiting_purchase_manager
#             if self.approval_stage == 'waiting_purchase_manager':
#                 if user.purchase_manager_from <= total <= user.purchase_manager_to:
#                     result = super().button_confirm()
#                     self._create_inventory_activity()
#                     self.approval_stage = "approved"
#                     return result
#                 else:
#                     raise UserError("المبلغ خارج صلاحياتك. برجاء تحويل الطلب للمدير المالي.")
#
#             raise UserError("ليست لديك صلاحية للتأكيد في هذه المرحلة.")
#
#         # ==========================================================
#         # 3) موظف مشتريات
#         # ==========================================================
#         if user.has_group("purchase.group_purchase_user"):
#
#             if self.approval_stage == 'none':
#                 if total <= user.purchase_user_limit:
#                     result = super().button_confirm()
#                     self._create_inventory_activity()
#                     self.approval_stage = "approved"
#                     return result
#                 else:
#                     raise UserError("المبلغ أكبر من صلاحيتك. برجاء تحويل الطلب لمدير المشتريات.")
#             else:
#                 raise UserError("ليست لديك صلاحية للتأكيد في هذه المرحلة.")
#
#         # ==========================================================
#         # 4) أي مستخدم آخر
#         # ==========================================================
#         raise UserError("ليست لديك صلاحية للتأكيد في هذه المرحلة.")
#
#     # ==========================
#     # Button visibility logic
#     # ==========================
#     @api.depends("amount_total", "approval_stage")
#     def _compute_visibility(self):
#         for rec in self:
#             user = rec.env.user
#             total = rec.amount_total
#
#             rec.can_send_to_manager = False
#             rec.can_send_to_finance = False
#             rec.can_manager_confirm = False
#             rec.can_finance_confirm = False
#
#             # ======================
#             # 1) المدير المالي
#             # ======================
#             if user.has_group("account.group_account_manager"):
#                 if rec.approval_stage == 'waiting_finance_manager':
#                     rec.can_finance_confirm = True
#                 continue
#
#             # ======================
#             # 2) مدير مشتريات (Administrator)
#             # ======================
#             if user.has_group("purchase.group_purchase_manager"):
#
#                 # مرحلة none → logic القفز للمالية
#                 if rec.approval_stage == 'none':
#                     if total > user.purchase_manager_to:
#                         rec.can_send_to_finance = True
#                     elif user.purchase_manager_from <= total <= user.purchase_manager_to:
#                         rec.can_manager_confirm = True
#                     continue
#
#                 # مرحلة انتظار مدير المشتريات
#                 if rec.approval_stage == 'waiting_purchase_manager':
#                     if user.purchase_manager_from <= total <= user.purchase_manager_to:
#                         rec.can_manager_confirm = True
#                     elif total > user.purchase_manager_to:
#                         rec.can_send_to_finance = True
#                 continue
#
#             # ======================
#             # 3) موظف مشتريات
#             # ======================
#             if user.has_group("purchase.group_purchase_user"):
#                 if rec.approval_stage == 'none' and total > user.purchase_user_limit:
#                     rec.can_send_to_manager = True
#                 continue
#
#     # ==========================
#     # Create Activities based on Stage
#     # ==========================
#     def _create_approval_activity(self, stage):
#         Activity = self.env['mail.activity']
#         Users = self.env['res.users']
#         _logger = self.env['ir.logging']
#
#         if stage == "waiting_purchase_manager":
#             target_users = Users.search([
#                 ('groups_id', 'in', self.env.ref('purchase.group_purchase_manager').id)
#             ])
#             summary = "مطلوب موافقة مدير المشتريات"
#             note = f"يرجى مراجعة أمر الشراء رقم {self.name}."
#
#         elif stage == "waiting_finance_manager":
#             target_users = Users.search([
#                 ('groups_id', 'in', self.env.ref('account.group_account_manager').id)
#             ])
#             summary = "مطلوب موافقة المدير المالي"
#             note = f"يرجى مراجعة أمر الشراء رقم {self.name}."
#
#         else:
#             return
#
#         self.message_post(body=f"🔔 بدء إنشاء Activities للمرحلة: {stage}")
#
#         for user in target_users:
#             Activity.create({
#                 'res_id': self.id,
#                 'res_model_id': self.env.ref('purchase.model_purchase_order').id,
#                 'user_id': user.id,
#                 'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
#                 'summary': summary,
#                 'note': note,
#             })
#
#             _logger.create({
#                 'name': 'Purchase Approval Activity',
#                 'type': 'server',
#                 'dbname': self._cr.dbname,
#                 'level': 'INFO',
#                 'message': f"Activity created for user: {user.name}",
#                 'path': 'purchase_order',
#                 'func': '_create_approval_activity',
#                 'line': '0',
#             })
#
#             self.message_post(body=f"✔ تم إرسال Activity إلى: <b>{user.name}</b>")
#
#         if not target_users:
#             self.message_post(body="⚠ لا يوجد مستخدمين مناسبين لهذه المرحلة!")
#
#     # ==========================
#     # Create Inventory Activities on Confirm
#     # ==========================
#     def _create_inventory_activity(self):
#         Activity = self.env['mail.activity']
#         Users = self.env['res.users']
#
#         inventory_users = Users.search([
#             ('groups_id', 'in', [
#                 self.env.ref('stock.group_stock_user').id,
#                 self.env.ref('stock.group_stock_manager').id
#             ])
#         ])
#
#         summary = "تنبيه لإدارة المخازن"
#         note = f"تم تأكيد أمر الشراء رقم {self.name}. يرجى بدء إجراءات الاستلام."
#
#         self.message_post(body="📦 بدء إرسال Activities للمخازن.")
#
#         for user in inventory_users:
#             Activity.create({
#                 'res_id': self.id,
#                 'res_model_id': self.env.ref('purchase.model_purchase_order').id,
#                 'user_id': user.id,
#                 'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
#                 'summary': summary,
#                 'note': note,
#             })
#
#             _logger.info(f"[INVENTORY ACTIVITY] Created for {user.name}")
#
#             self.message_post(body=f"✔ تم إرسال Activity لمستخدم المخازن: <b>{user.name}</b>")
#
#         if not inventory_users:
#             self.message_post(body="⚠ لا يوجد مستخدمين في قسم المخازن!")
#
#
#
#
#
#
#
#
#
#
#
# class StockPicking(models.Model):
#     _inherit = "stock.picking"
#
#     # ==========================================================
#     # Override button_validate → بعد كل Validate نرسل Activity للمحاسبين
#     # ==========================================================
#     def button_validate(self):
#         result = super().button_validate()
#
#         for picking in self:
#             picking._create_accounting_activity()
#
#         return result
#
#     # ==========================================================
#     # Create Activity for all Accounting users
#     # ==========================================================
#     def _create_accounting_activity(self):
#         Activity = self.env['mail.activity']
#         Users = self.env['res.users']
#
#         # جروبات الـ Accounting الموجودة فعلياً في Odoo 18
#         accounting_groups = [
#             'account.group_account_readonly',
#             'account.group_account_invoice',
#             'account.group_account_user',
#             'account.group_account_manager',
#         ]
#
#         # الحصول على الـ IDs فقط للجروبات الموجودة
#         group_ids = []
#         for g in accounting_groups:
#             try:
#                 group_ids.append(self.env.ref(g).id)
#             except:
#                 _logger.warning(f"[WARNING] Group not found: {g}")
#
#         # كل المستخدمين الذين ينتمون لأي جروب من الجروبات دي
#         target_users = Users.search([('groups_id', 'in', group_ids)])
#
#         summary = "حركة مخزون جديدة تم اعتمادها"
#         note = f"تم عمل Validate للحركة: {self.name}. يرجى المتابعة من قسم الحسابات."
#
#         # يظهر في الشات
#         self.message_post(body="📦 تم عمل Validate للحركة، وإرسال Activities للمحاسبين.")
#
#         # إنشاء Activity لكل مستخدم
#         for user in target_users:
#             Activity.create({
#                 'res_id': self.id,
#                 'res_model_id': self.env.ref('stock.model_stock_picking').id,
#                 'user_id': user.id,
#                 'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
#                 'summary': summary,
#                 'note': note,
#             })
#
#             _logger.info(f"[ACCOUNTING ACTIVITY] Created for accounting user: {user.name}")
#
#             self.message_post(
#                 body=f"✔ تم إرسال Activity لمستخدم الحسابات: <b>{user.name}</b>"
#             )
#
#         if not target_users:
#             self.message_post(body="⚠ لا يوجد مستخدمين في قسم المحاسبة!")
