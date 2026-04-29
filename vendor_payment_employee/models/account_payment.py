from odoo import models, fields, api
from odoo.exceptions import ValidationError

ALLOWED_COMPANY_REGISTRIES = ["7012242793", "1010232192","311369490700003"]   # ✅ المتغير الوحيد المستخدم الآن


class AccountPayment(models.Model):
    _inherit = "account.payment"



    # ================= Employee =================
    employee_id = fields.Many2one(
        "hr.employee",
        string="Beneficiary",
        required=True
    )
    project_id = fields.Many2one(
        "project.project",
        string="Project"
    )

    department_id = fields.Many2one(
        "hr.department",
        related="employee_id.department_id",
        store=True,
        readonly=True
    )

    show_employee_fields = fields.Boolean(
        compute="_compute_show_employee_fields",
        store=False
    )
    current_user_allow_payment_confirm = fields.Boolean(
        compute="_compute_current_user_allow_payment_confirm",
        store=False
    )

    def _compute_current_user_allow_payment_confirm(self):
        user = self.env.user
        for rec in self:
            rec.current_user_allow_payment_confirm = user.allow_payment_confirm

    # ================= Custom Workflow (SAFE) =================
    request_state = fields.Selection(
        [
            ("draft", "created"),
            ("requested", "Requested"),
            ('manager', 'Purchase Manager'),
            ('accounting', 'Accounting Approval'),
            ('ceo', 'CO Confirmation'),
        ],
        string="Request Status",
        default="draft",
        tracking=True
    )

    # ================= Report Safe Fields =================
    report_employee_name = fields.Char(
        compute="_compute_report_header",
        store=False
    )

    report_department_name = fields.Char(
        compute="_compute_report_header",
        store=False
    )

    kind_of_payment_id = fields.Many2one(
        "kind.of.payment",
        string="Kind of Payment"
    )

    custom_sequence = fields.Char(
        string="Payment Reference",
        readonly=True,
        copy=False
    )
    requester_user_id = fields.Many2one(
        "res.users", string="Requested By", readonly=True
    )
    manager_user_id = fields.Many2one(
        "res.users", string="Manager Approved By", readonly=True
    )
    accounting_user_id = fields.Many2one(
        "res.users", string="Accounting Approved By", readonly=True
    )
    ceo_user_id = fields.Many2one(
        "res.users", string="COO Approved By", readonly=True
    )

    payment_type_display = fields.Selection(
        selection=[('inbound', 'Inbound'), ('outbound', 'Outbound')],
        string="Payment Type",
        compute="_compute_payment_type_display",
        store=False,
    )

    @api.depends('payment_type')
    def _compute_payment_type_display(self):
        for rec in self:
            if rec.payment_type == 'outbound':
                rec.payment_type_display = rec.payment_type if rec.payment_type == 'outbound' else 'outbound'
            else:
                rec.payment_type_display = rec.payment_type


    
    def action_manager_approve(self):
        for rec in self:
            if rec.request_state != 'requested':
                raise ValidationError("Payment must be Requested before Purchase Manager Approval.")

            rec.write({
            "request_state": "manager",
            "manager_user_id": self.env.user.id,
        })
            rec.message_post(
                body=f"Payment approved by Manager: {self.env.user.name}"
            )

    def action_accounting_approve(self):
        for rec in self:
            if rec.request_state != 'manager':
                raise ValidationError("Payment must be Purchase Manager approved before Accounting Approval.")
            rec.write({
            "request_state": "accounting",
            "accounting_user_id": self.env.user.id,
        })

        rec.message_post(body=f"Payment approved by Accounting: {self.env.user.name}")

    def action_ceo_confirm(self):
        for rec in self:
            if rec.request_state != 'accounting':
                raise ValidationError("Payment must be Accounting Approved before CO Confirmation.")
            
            rec.write({
            "request_state": "ceo",
            "ceo_user_id": self.env.user.id,
        })

        rec.message_post(body=f"Payment confirmed by CO: {self.env.user.name}")




    # ================= Computes =================
    @api.depends("employee_id", "department_id")
    def _compute_report_header(self):
        for rec in self:
            rec.report_employee_name = ""
            rec.report_department_name = ""

            if rec.employee_id:
                rec.report_employee_name = rec.employee_id.sudo().name or ""

            if rec.department_id:
                rec.report_department_name = rec.department_id.sudo().name or ""

    @api.depends("company_id")
    def _compute_show_employee_fields(self):
        for rec in self:
            rec.show_employee_fields = bool(
                rec.company_id
                and rec.company_id.company_registry in ALLOWED_COMPANY_REGISTRIES   # ✅ بدل TARGET
            )

    # ================= Actions =================
    def action_request_payment(self):
        for rec in self:
            
            # 🔑 مهم: تأكيد إن الريكورد محفوظ
            if not rec.id:
                rec.flush()

            if rec.request_state != "draft":
                return

            if not rec.custom_sequence:
                seq = self.env["ir.sequence"].next_by_code(
                    "account.payment.prh"
                )
                rec.write({
                    "custom_sequence": seq,
                    "requester_user_id": self.env.user.id,
                    "request_state": "requested",
                })

            rec.message_post(body=f"Payment requested by {self.env.user.name}")

    def action_post(self):
        """
        Confirm payment (Odoo native)
        """
        for rec in self:
            if not self.env.user.allow_payment_confirm:
                raise ValidationError(
                    "You are not allowed to confirm payments."
                )

            # Ensure sequence exists before posting
            if not rec.custom_sequence:
                seq = self.env["ir.sequence"].next_by_code(
                    "account.payment.prh"
                )
                rec.custom_sequence = seq

        res = super().action_post()
        return res



