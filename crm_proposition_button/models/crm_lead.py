from odoo import models, fields, api
from odoo.exceptions import UserError

ARKA_COMPANY_REGISTRY = "311369490700003"

from odoo import models, fields, api


class CrmStageWizard(models.TransientModel):
    _name = "crm.stage.wizard"
    _description = "CRM Stage Wizard"

    user_ids = fields.Many2many('res.users', string="Assign Users")

    action_type = fields.Selection([
        ('technical', 'Technical Office'),
        ('project', 'Project Management'),
        ('designer', 'Designer'),  # 👈 ضيف دي

    ])

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['action_type'] = self.env.context.get('default_action_type')
        return res

    def action_confirm(self):
        lead = self.env['crm.lead'].browse(self.env.context.get('active_id'))

        if self.action_type == 'technical':
            lead.action_move_to_proposition()

        elif self.action_type == 'project':
            lead.action_move_to_project_management()

        elif self.action_type == 'designer':  # 👈 ضيف دي
            lead.action_move_to_designer()

        for user in self.user_ids:
            self.env['mail.activity'].create({
                'res_model_id': self.env['ir.model']._get_id('crm.lead'),
                'res_id': lead.id,
                'user_id': user.id,
                'summary': "New Task Assigned",
                'note': "You have a new lead to handle",
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            })

        return {'type': 'ir.actions.act_window_close'}

class CrmLead(models.Model):
    _inherit = "crm.lead"
    hide_all_buttons_pm = fields.Boolean(compute="_compute_hide_all_buttons_pm")

    @api.depends_context("in_projects_management")
    def _compute_hide_all_buttons_pm(self):
        for rec in self:
            rec.hide_all_buttons_pm = bool(self.env.context.get("in_projects_management"))

    is_arka_company = fields.Boolean(
        compute="_compute_is_arka_company",
        store=False
    )

    def _compute_is_arka_company(self):
        for rec in self:
            rec.is_arka_company = rec.env.company.company_registry == ARKA_COMPANY_REGISTRY

    def action_move_to_proposition(self):
        company = self.env.company

        # Only ARKA
        if company.company_registry != ARKA_COMPANY_REGISTRY:
            raise UserError("This action is only available for ARKA company.")

        CRMTeam = self.env['crm.team']

        # get or create Sales Team
        team = CRMTeam.search([('company_id', '=', company.id)], limit=1)
        if not team:
            team = CRMTeam.create({
                'name': f"{company.name} Sales Team",
                'company_id': company.id,
            })

        Stage = self.env['crm.stage']

        # ============================================================
        # 1) Get NEW stage for this team — or global NEW if not exist
        # ============================================================

        # try team-specific New
        stage_new = Stage.search([
            ('name', '=', 'New'),
            ('team_id', '=', team.id),
        ], limit=1)

        # if not found — try global New
        if not stage_new:
            stage_new = Stage.search([
                ('name', '=', 'New'),
                ('team_id', '=', False),
            ], limit=1)

        # if still not found — create it
        if not stage_new:
            stage_new = Stage.create({
                'name': 'New',
                'sequence': 1,
                'team_id': team.id,
            })

        # ============================================================
        # 2) Get/Make "Technical Office" stage (after New)
        # ============================================================
        stage_prop = Stage.search([
            ('name', '=', 'Technical Office'),
            '|',
            ('team_id', '=', team.id),
            ('team_id', '=', False),
        ], limit=1)

        # لو مش موجود → اعمله
        if not stage_prop:
            stage_prop = Stage.create({
                'name': 'Technical Office',
                'sequence': stage_new.sequence + 1,
                'team_id': team.id,
            })
        else:
            # اضبط ترتيبه بالنسبة لـ New
            stage_prop.sequence = stage_new.sequence + 1

        # ============================================================
        # 3) Move lead to Technical Office
        # ============================================================
        self.write({'stage_id': stage_prop.id})

        return True

    def action_move_to_project_management(self):
        company = self.env.company

        # Only ARKA
        if company.company_registry != ARKA_COMPANY_REGISTRY:
            raise UserError("This action is only available for ARKA company.")

        CRMTeam = self.env['crm.team']

        # get or create Sales Team
        team = CRMTeam.search([('company_id', '=', company.id)], limit=1)
        if not team:
            team = CRMTeam.create({
                'name': f"{company.name} Sales Team",
                'company_id': company.id,
            })

        Stage = self.env['crm.stage']

        # ============================================================
        # 1) Get NEW stage for this team — or global NEW if not exist
        # ============================================================

        # try team-specific New
        stage_new = Stage.search([
            ('name', '=', 'New'),
            ('team_id', '=', team.id),
        ], limit=1)

        # if not found — try global New
        if not stage_new:
            stage_new = Stage.search([
                ('name', '=', 'New'),
                ('team_id', '=', False),
            ], limit=1)

        # if still not found — create it
        if not stage_new:
            stage_new = Stage.create({
                'name': 'New',
                'sequence': 1,
                'team_id': team.id,
            })

        # ============================================================
        # 2) Get/Make "Technical Office" stage (after New)
        # ============================================================
        stage_prop = Stage.search([
            ('name', '=', 'Projects Management'),
            '|',
            ('team_id', '=', team.id),
            ('team_id', '=', False),
        ], limit=1)

        # لو مش موجود → اعمله
        if not stage_prop:
            stage_prop = Stage.create({
                'name': 'Projects Management',
                'sequence': stage_new.sequence + 2,
                'team_id': team.id,
            })
        else:
            # اضبط ترتيبه بالنسبة لـ New
            stage_prop.sequence = stage_new.sequence + 2

        # ============================================================
        # 3) Move lead to Technical Office
        # ============================================================
        self.write({'stage_id': stage_prop.id})
        self.milestone_group_ids.action_to_project()

        return True

    is_stage_new = fields.Boolean(compute="_compute_stage_flags", store=False)
    is_stage_technical = fields.Boolean(compute="_compute_stage_flags", store=False)
    is_stage_designer = fields.Boolean(compute="_compute_stage_flags", store=False)

    def _compute_stage_flags(self):
        for rec in self:
            rec.is_stage_new = rec.stage_id.name == "New"
            rec.is_stage_technical = rec.stage_id.name == "Technical Office"
            rec.is_stage_designer = rec.stage_id.name == "Designer"

    show_button_allowed = fields.Boolean(compute="_compute_button_visibility")

    def _compute_button_visibility(self):
        for rec in self:
            rec.show_button_allowed = rec.env.user.show_project_button

    show_designer_button = fields.Boolean(
        compute="_compute_designer_button"
    )

    def _compute_designer_button(self):
        for rec in self:
            rec.show_designer_button = rec.env.user.show_move_to_designer

    def action_move_to_designer(self):
        company = self.env.company
        CRMTeam = self.env['crm.team']
        Stage = self.env['crm.stage']

        team = CRMTeam.search([('company_id', '=', company.id)], limit=1)
        if not team:
            team = CRMTeam.create({
                'name': f"{company.name} Sales Team",
                'company_id': company.id,
            })

        # حاول تجيب Stage Designer
        stage_designer = Stage.search([
            ('name', '=', 'Designer'),
            '|',
            ('team_id', '=', team.id),
            ('team_id', '=', False),
        ], limit=1)

        if not stage_designer:
            stage_designer = Stage.create({
                'name': 'Designer',
                'sequence': 50,
                'team_id': team.id,
            })

        self.write({'stage_id': stage_designer.id})
        return True

    show_proposition_button = fields.Boolean(
        compute="_compute_proposition_button"
    )

    def _compute_proposition_button(self):
        for rec in self:
            rec.show_proposition_button = rec.env.user.show_move_to_proposition


class ResUsers(models.Model):
    _inherit = "res.users"

    show_project_button = fields.Boolean(
        string="Show Move to Project Button",
        default=False,
        help="If enabled, the user will see the 'Move to Project Management' button."
    )
    show_move_to_designer = fields.Boolean(
        string="Show Move to Designer Button",
        default=False,
        help="If enabled, user will see Move to Designer button in CRM."
    )

    show_move_to_proposition = fields.Boolean(
        string="Show Move to Technical Office Button",
        default=False,
        help="If enabled, user will see Move to Technical Office button."
    )
