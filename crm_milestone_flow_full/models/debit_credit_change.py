from odoo import models, api, fields, _
from odoo.exceptions import UserError


# =========================================================
# MILESTONE ACCOUNT CONFIG
# =========================================================

class MilestoneAccountConfig(models.Model):
    _name = "milestone.account.config"
    _description = "Milestone Accounting Configuration"

    name = fields.Char(required=True)

    po_type = fields.Selection([
        ('inventory', "With Inventory Material"),
        ('non_inventory', "Non Inventory Material"),
        ('service', "Service"),
    ], required=True)

    debit_account_id = fields.Many2one(
        "account.account",
        string="Debit Account",
    )

    credit_account_id = fields.Many2one(
        "account.account",
        string="Credit Account",
    )

    vendor_bill_account_id = fields.Many2one(
        "account.account",
        string="Vendor Bill Account"
    )


# =========================================================
# JOB ORDER ACCOUNT CONFIG
# =========================================================

class JobOrderAccountConfig(models.Model):
    _name = "job.order.account.config"
    _description = "Job Order Accounting Configuration"

    name = fields.Char(required=True)

    job_type = fields.Selection([
        ('internal', "Internal Manufacturing Order"),
        ('sub_with', "Subcontractor (with material)"),
        ('sub_without', "Subcontractor (without material)")
    ], required=True)

    # Existing fields (لم نحذفهم)
    debit_account_id = fields.Many2one(
        "account.account",
        string="Debit Account",
    )

    credit_account_id = fields.Many2one(
        "account.account",
        string="Credit Account",
    )

    vendor_bill_account_id = fields.Many2one(
        "account.account",
        string="Vendor Bill Account"
    )

    # 🔴 NEW FIELDS (MO Accounts)

    mo_debit_account_id = fields.Many2one(
        "account.account",
        string="MO Debit Account"
    )

    mo_credit_account_id = fields.Many2one(
        "account.account",
        string="MO Credit Account"
    )

    # 🔴 NEW FIELDS (PO Accounts)

    po_debit_account_id = fields.Many2one(
        "account.account",
        string="PO Debit Account"
    )

    po_credit_account_id = fields.Many2one(
        "account.account",
        string="PO Credit Account"
    )


# =========================================================
# PURCHASE ORDER EXTENSION
# =========================================================

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    milestone_po = fields.Boolean()

    milestone_type = fields.Selection([
        ('inventory', "With Inventory Material"),
        ('non_inventory', "Non Inventory Material"),
        ('service', "Service"),
    ])

    job_order_generated = fields.Boolean()
    job_order_type = fields.Selection([
        ('internal', "Internal Manufacturing Order"),
        ('sub_with', "Subcontractor (with material)"),
        ('sub_without', "Subcontractor (without material)")
    ])


# =========================================================
# MRP PRODUCTION EXTENSION
# =========================================================

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    job_order_generated = fields.Boolean()

    job_order_type = fields.Selection([
        ('internal', "Internal Manufacturing Order"),
        ('sub_with', "Subcontractor (with material)"),
        ('sub_without', "Subcontractor (without material)")
    ])


# =========================================================
# STOCK MOVE ACCOUNTING (MILESTONE + JOB ORDER)
# =========================================================

class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_line(
        self,
        qty,
        cost,
        credit_account_id,
        debit_account_id,
        svl_id,
        description,
    ):

        # =====================================================
        # MILESTONE PURCHASE ACCOUNTING
        # =====================================================

        picking = self.picking_id
        po = picking.purchase_id if picking else False

        if po and po.milestone_po:

            config = self.env["milestone.account.config"].search([
                ("po_type", "=", po.milestone_type)
            ], limit=1)

            if config:
                credit_account_id = config.credit_account_id.id
                debit_account_id = config.debit_account_id.id

        # =====================================================
        # JOB ORDER PO ACCOUNTING
        # =====================================================

        if po and po.job_order_generated:

            config = self.env["job.order.account.config"].search([
                ("job_type", "=", po.job_order_type)
            ], limit=1)

            if config:

                if config.po_debit_account_id:
                    debit_account_id = config.po_debit_account_id.id

                if config.po_credit_account_id:
                    credit_account_id = config.po_credit_account_id.id

        # =====================================================
        # JOB ORDER MO ACCOUNTING
        # =====================================================

        production = self.raw_material_production_id

        if production and production.job_order_generated:

            config = self.env["job.order.account.config"].search([
                ("job_type", "=", production.job_order_type)
            ], limit=1)

            if config:

                if config.mo_debit_account_id:
                    debit_account_id = config.mo_debit_account_id.id

                if config.mo_credit_account_id:
                    credit_account_id = config.mo_credit_account_id.id

        # =====================================================
        # GET PROJECT ANALYTIC ACCOUNT
        # =====================================================

        analytic_distribution = {}

        project = False

        # From Purchase Order
        if po and po.project_id:
            project = po.project_id

        # From Manufacturing Order
        if production and production.project_id:
            project = production.project_id

        if project and project.account_id:
            analytic_distribution = {project.account_id.id: 100}

        # =====================================================
        # CREATE ACCOUNT MOVE LINES
        # =====================================================

        res = super()._prepare_account_move_line(
            qty,
            cost,
            credit_account_id,
            debit_account_id,
            svl_id,
            description,
        )

        # Add analytic distribution
        if analytic_distribution:
            for line in res:
                if isinstance(line, tuple) and len(line) == 3:
                    line[2]["analytic_distribution"] = analytic_distribution

        return res
# =========================================================
# ACCOUNT MOVE LINE (VENDOR BILL)
# =========================================================

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):

        lines = super().create(vals_list)

        for line in lines:

            if line.move_id.move_type != "in_invoice":
                continue

            po = line.purchase_line_id.order_id if line.purchase_line_id else False

            # =====================================================
            # MILESTONE VENDOR BILL ACCOUNT
            # =====================================================

            if po and po.milestone_po:

                config = self.env["milestone.account.config"].search([
                    ("po_type", "=", po.milestone_type)
                ], limit=1)

                if config and config.vendor_bill_account_id:
                    line.account_id = config.vendor_bill_account_id.id

            # =====================================================
            # JOB ORDER VENDOR BILL ACCOUNT
            # =====================================================

            if po and po.job_order_generated:

                config = self.env["job.order.account.config"].search([
                    ("job_type", "=", po.job_order_type)
                ], limit=1)

                if config and config.vendor_bill_account_id:
                    line.account_id = config.vendor_bill_account_id.id

        return lines


# =========================================================
# INTERNAL TRANSFER
# =========================================================

class StockLocation(models.Model):
    _inherit = "stock.location"

    milestone_location = fields.Boolean(
        string="Milestone Location"
    )


class InternalTransferAccount(models.Model):
    _name = "milestone.internal.transfer.account"

    name = fields.Char(default="Internal Transfer Accounts")

    debit_account_id = fields.Many2one(
        "account.account",
        required=True
    )

    credit_account_id = fields.Many2one(
        "account.account",
        required=True
    )


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):

        res = super().button_validate()

        for picking in self:

            if picking.picking_type_id.code != "internal":
                continue

            src = picking.location_id
            dest = picking.location_dest_id

            if not (src.milestone_location or dest.milestone_location):
                continue

            config = self.env["milestone.internal.transfer.account"].search([], limit=1)

            if not config:
                continue

            amount = 0

            for move in picking.move_ids:
                cost = move.product_id.standard_price
                qty = sum(move.move_line_ids.mapped("qty_done"))
                amount += cost * qty

            if not amount:
                continue

            journal = self.env["account.journal"].search(
                [("type", "=", "general")], limit=1
            )

            if dest.milestone_location:
                debit_account = config.debit_account_id
                credit_account = config.credit_account_id

            elif src.milestone_location:
                debit_account = config.credit_account_id
                credit_account = config.debit_account_id

            else:
                continue

            move_vals = {
                "journal_id": journal.id,
                "ref": picking.name,
                "line_ids": [
                    (0, 0, {
                        "account_id": debit_account.id,
                        "debit": amount,
                        "credit": 0,
                        "name": picking.name,
                    }),
                    (0, 0, {
                        "account_id": credit_account.id,
                        "debit": 0,
                        "credit": amount,
                        "name": picking.name,
                    }),
                ]
            }

            move = self.env["account.move"].create(move_vals)
            move.action_post()

        return res