from odoo import models, fields, api



class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    kind_of_payment_id = fields.Many2one(
        "kind.of.payment",
        string="Kind of Payment"
    )



    state = fields.Selection(
        selection=[
            ('draft', 'Created'),     
            ('submit', 'Requested'),         
            ('approve', 'Manager Approved'),  
            ('post', 'Accounting '),
            ('ceo', 'CEO Confirmed'),    
            ('done', 'paid'),            
        ],
        string="Status",
        readonly=True,
        copy=False,
        tracking=True,
    )



    custom_sequence = fields.Char(
        string="Expense Reference",
        readonly=True,
        copy=False
    )
    project_id = fields.Many2one(
        "project.project",
        string="Project",
    )

    @api.model
    def create(self, vals):
        if not vals.get("custom_sequence"):
            vals["custom_sequence"] = self.env["ir.sequence"].next_by_code(
                "hr.expense.prex"
            )
        return super().create(vals)
    
    def action_ceo_approve_expense_sheets(self):
        for rec in self:
            if rec.state != 'post':
                raise ValueError("Only expenses in 'Accounting' state can be CEO approved.")
            rec.state = 'ceo'

