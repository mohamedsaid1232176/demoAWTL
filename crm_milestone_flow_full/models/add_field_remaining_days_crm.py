from odoo import models, fields
from datetime import timedelta


class CrmLead(models.Model):
    _inherit = "crm.lead"

    remaining_days = fields.Integer(
        string="Reminder Before End (Days)",
        help="Send daily activity during the last X days before end date"
    )

    def _send_project_manager_activity(self):
        Activity = self.env["mail.activity"]
        activity_type = self.env.ref("mail.mail_activity_data_todo")
        today = fields.Date.today()

        leads = self.search([
            ("remaining_days", ">", 0),
            ("date_end", "!=", False),
            ("project_manager_ids", "!=", False),
        ])

        for lead in leads:
            start_date = lead.date_end - timedelta(days=lead.remaining_days)

            # ✅ آخر X أيام قبل النهاية
            if start_date <= today < lead.date_end:
                for user in lead.project_manager_ids:

                    # منع تكرار Activity في نفس اليوم
                    existing_activity = Activity.search([
                        ("res_model", "=", "crm.lead"),
                        ("res_id", "=", lead.id),
                        ("user_id", "=", user.id),
                        ("activity_type_id", "=", activity_type.id),
                        ("date_deadline", "=", today),
                    ], limit=1)

                    if not existing_activity:
                        Activity.create({
                            "activity_type_id": activity_type.id,
                            "res_model_id": self.env["ir.model"]._get_id("crm.lead"),
                            "res_id": lead.id,
                            "user_id": user.id,
                            "summary": "Project end reminder",
                            "note": (
                                f"Project will end on {lead.date_end}. "
                                f"Daily reminder during last {lead.remaining_days} days."
                            ),
                            "date_deadline": today,
                        })
