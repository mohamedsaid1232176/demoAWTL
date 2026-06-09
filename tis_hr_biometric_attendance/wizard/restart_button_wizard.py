# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields

class RestartButtonWizard(models.TransientModel):
    _name = 'restart.button.wizard'
    _description = 'Restart Button Wizard'

    device_id = fields.Many2one('biometric.config', string="Device", required=True)  # Replace with correct model

    warning_msg = fields.Text(
        string="Warning",
        default="Do you want to restart the device?"
    )

    def confirm_restart(self):
        for wizard in self:
            command = self.env['device.command'].create({
                'name': 'REBOOT',
                'device_id': wizard.device_id.id,
                'status': 'pending'
            })
            command.execution_log = f"C:{command.id}:REBOOT\n"
        return {'type': 'ir.actions.act_window_close'}
