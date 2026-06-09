# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import re


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    biometric_device_ids = fields.One2many('biometric.attendance.devices', 'employee_id', string='Biometric Devices')

    def create_export_command(self, device_id):
        command_id = self.env['device.command'].sudo().search([('employee_id', '=', self.id),
                                                               ('device_id', '=', device_id.id),
                                                               ('name', '=', 'DATA'),
                                                               ('status', '=', 'pending')])
        if not command_id:
            list_user_ids = self.env['biometric.attendance.devices'].sudo().search(
                [('device_id', '=', device_id.id)]).mapped('biometric_attendance_id')
            user_id_items = [item for item in list_user_ids]
            pending_user_pin_ids = self.env['device.command'].search([('device_id', '=', device_id.id),
                                                                      ('status', '!=', 'success'),
                                                                      ('pin', '!=', False)]).mapped('pin')

            tot_user_id_items = user_id_items + pending_user_pin_ids
            next_user_id = self.get_next_user_id(tot_user_id_items)
            command_id = self.env['device.command'].sudo().create({
                'name': 'DATA',
                'device_id':device_id.id,
                'employee_id': self.id,
                'status':'pending',
            })
            card_number = self.barcode if self.barcode else "0000000000"
            command_id.execution_log = f"C:{command_id.id}:DATA USER PIN={next_user_id}	Name={self.name}	Pri=0	Passwd=	Card=[{card_number}]	Grp=1	TZ=0000000000000000\n"
            command_id.pin = next_user_id
        else:
            raise UserError(_("Command already created."))

    def get_next_user_id(self, user_ids: list) -> str:
        """
        Generates the next user ID based on a list of existing user IDs.
        If all IDs are numeric, returns the next highest integer.
        If IDs are alphanumeric, increments the highest numeric suffix or appends '1'.
        """
        if not user_ids:
            return "2"  # Default start if no IDs exist

        numeric_ids = [int(uid) for uid in user_ids if uid.isdigit()]
        alphanumeric_ids = [uid for uid in user_ids if not uid.isdigit()]

        if numeric_ids:
            return str(max(numeric_ids) + 1)

        pattern = re.compile(r"(\D*)(\d*)")
        parsed_ids = [pattern.match(uid).groups() for uid in alphanumeric_ids]

        prefix_groups = {}
        for prefix, number in parsed_ids:
            number = int(number) if number else 0
            if prefix in prefix_groups:
                prefix_groups[prefix].append(number)
            else:
                prefix_groups[prefix] = [number]

        most_common_prefix = max(prefix_groups,
                                 key=lambda k: len(prefix_groups[k]))
        next_number = max(prefix_groups[most_common_prefix]) + 1 if \
        prefix_groups[most_common_prefix] else 1

        return f"{most_common_prefix}{next_number}"



    def employee_del_command(self, device_id):
        command_id = self.env['device.command'].sudo().search(
            [('employee_id', '=', self.id),
             ('device_id', '=', device_id.id),
             ('name', '=', 'DEL'),
             ('status', '=', 'pending')])
        if not command_id:
            device_user_id = self.biometric_device_ids.filtered(lambda x:x.device_id == device_id)
            if device_user_id:
                command_id = self.env['device.command'].sudo().create({
                    'name': 'DEL',
                    'device_id': device_id.id,
                    'employee_id': self.id,
                    'status': 'pending',
                })
                command_id.execution_log = f"C:{command_id.id}:DATA DEL_USER PIN={device_user_id.biometric_attendance_id} \n"
                command_id.pin = device_user_id.biometric_attendance_id
            else:
                raise UserError(_("The employee is not registered on the device."))
        else:
            raise UserError(_("User delete command already created."))

    def update_export_command(self, device_id):
        command_id = self.env['device.command'].sudo().search([('employee_id', '=', self.id),
                                                               ('device_id', '=', device_id.id),
                                                               ('name', '=', 'UPDATE'),
                                                               ('status', '=', 'pending')])
        if not command_id:
            device_user_id = self.biometric_device_ids.filtered(lambda x:x.device_id == device_id)
            command_id = self.env['device.command'].sudo().create({
                'name': 'UPDATE',
                'device_id':device_id.id,
                'employee_id': self.id,
                'status':'pending',
            })
            command_id.execution_log = f"C:{command_id.id}:DATA USER PIN={device_user_id.biometric_attendance_id}	Name={self.name} \n"
            command_id.pin = device_user_id.biometric_attendance_id
        else:
            raise UserError(_("Command already created."))

class BiometricAttendanceDevices(models.Model):
    _name = 'biometric.attendance.devices'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'biometric attendance devices'
    _rec_name = 'biometric_attendance_id'

    device_user_name = fields.Char()
    employee_id = fields.Many2one('hr.employee', string='Employee')
    biometric_attendance_id = fields.Char(string='Biometric User ID', required=True)
    device_id = fields.Many2one('biometric.config', string='Biometric Attendance Device', required=True,
                                ondelete='cascade')
    finger_template_ids = fields.One2many(
        'finger.template',  # Target model
        'device_user_id',  # Inverse field in finger.template
    )
    command_count = fields.Integer(
        string="Command Count",
        compute="_compute_command_count"
    )

    def action_user_commands(self):
        """This method returns an action that displays the attendance data log records
           filtered by the current device and user pin."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Command To Device',
            'view_mode': 'list,form',
            'res_model': 'device.command',
            'domain': [
                ('device_id', '=', self.device_id.id),
                ('pin', '=', self.biometric_attendance_id)
            ],
            'context': dict(self.env.context, default_device_id=self.device_id.id,
                            default_pin=self.biometric_attendance_id),
        }

    @api.depends('device_id', 'biometric_attendance_id')
    def _compute_command_count(self):
        """Computes the number of device commands associated with the current device and biometric attendance ID."""
        for rec in self:
            if rec.device_id and rec.biometric_attendance_id:
                rec.command_count = self.env['device.command'].sudo().search_count([
                    ('device_id', '=', rec.device_id.id),
                    ('pin', '=', rec.biometric_attendance_id)
                ])
            else:
                rec.command_count = 0

    def enroll_finger_print(self):
        """Enrolls a new fingerprint for the user and constructs the corresponding command."""
        self.ensure_one()

        if self.device_id.is_adms:
            # Get the highest FID
            enrolled_fingers = self.finger_template_ids
            if enrolled_fingers:
                # Find the next available FID by looking at the current FID values
                existing_fids = [finger.f_id for finger in enrolled_fingers]
                next_fid = max(existing_fids) + 1
            else:
                next_fid = 0  # Start with FID 0 if no fingers are enrolled yet

            print(f"Next available FID: {next_fid}")

            if next_fid >= 10:
                raise UserError("Maximum number of fingerprints (10) have already been enrolled.")

            # Create the command record
            command_id = self.env['device.command'].sudo().create({
                'name': 'ENROLL_FP',
                'device_id': self.device_id.id,
                'pin': self.biometric_attendance_id,
            })

            # Construct the command to enroll the fingerprint
            command_text = f"C:{command_id.id}:ENROLL_FP PIN={self.biometric_attendance_id}\tFID={next_fid}\tRETRY=1\tOVERWRITE=1\n"
            command_id.execution_log = command_text

            return True

        else:
            # Handle the case where the device is not using ADMS
            raise UserError("Enrollment is only supported on ADMS-connected devices.")
