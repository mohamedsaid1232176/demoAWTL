from odoo import fields,models
from datetime import datetime,timedelta

class AttendanceAdmsDownloadWizard(models.TransientModel):
    _name = 'attendance.adms.download.wizard'
    _description = 'ADMS Attendance Download Wizard'

    start_date = fields.Datetime(string='Start Time',
                                 required=True,
                                 default=lambda self: datetime.combine(fields.Date.context_today(self),
                                                                       datetime.min.time())
                                 )
    end_date = fields.Datetime(string='End Time',
                               required=True,
                               default=lambda self: datetime.combine(fields.Date.context_today(self) + timedelta(days=1), datetime.min.time()))
    device_id = fields.Many2one('biometric.config', string='Device', required=True)

    def action_submit(self):
        for wizard in self:
            start = wizard.start_date.strftime('%Y-%m-%d %H:%M:%S')
            end = wizard.end_date.strftime('%Y-%m-%d %H:%M:%S')

            command = self.env['device.command'].create({
                'name': 'ATTLOG',
                'device_id': wizard.device_id.id,
                'status': 'pending',
                'execution_log': '',  # initially blank
            })

            command.execution_log = f"C:{command.id}:DATA QUERY ATTLOG StartTime={start}    EndTime={end}\n "

        return {'type': 'ir.actions.act_window_close'}
