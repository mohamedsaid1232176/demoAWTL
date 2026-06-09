# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from datetime import datetime
import pytz
from odoo import models, fields,_
from odoo.exceptions import UserError

class AttendanceWizard(models.TransientModel):
    _name = 'attendance.calc.wizard'
    _description = 'attendance calc wizard'

    def calculate_attendance(self):
        minimal_attendance = self.env['ir.config_parameter'].sudo().get_param(
            'tis_hr_biometric_attendance.minimal_attendance')
        hr_attendance = self.env['hr.attendance']
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        domain = [('punching_time', '<=', str(today)), ('is_calculated', '=', False)]
        attendance_log = self.env['attendance.log'].search(domain).sorted('punching_time')
        logs_without_employee = attendance_log.filtered(
            lambda log: not log.employee_id)
        if logs_without_employee:
            raise UserError(_(
                "Some attendance logs do not have an associated employee!\n\n"
                "Please go to:\n"
                "Biometric Device Config -> Select Device -> Users\n"
                "Then, map the employee in device users."
            ))
        for log in attendance_log:
            if minimal_attendance:
                attendance = self.env['hr.attendance'].search(
                    [('employee_id', '=', log.employee_id.id),
                     ('punch_date', '=', log.punching_time.date())])
                if attendance:
                    attendance.write({'check_out': log.punching_time})
                else:
                    last_attendance_before_check_out = self.env['hr.attendance'].search([
                        ('employee_id', '=', log.employee_id.id),
                        ('check_out', '=', False)
                    ], order='check_in desc', limit=1)
                    if last_attendance_before_check_out:
                        check_out_time = last_attendance_before_check_out.check_in.replace(hour=23, minute=59,
                                                                                           second=59)
                        local_tz = pytz.timezone(log.device_user_id.device_id.time_zone or 'GMT')
                        local_dt = local_tz.localize(check_out_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                        check_out_time = datetime.strptime(utc_dt,
                                                       "%Y-%m-%d %H:%M:%S")
                        check_out_time = fields.Datetime.to_string(check_out_time)
                        last_attendance_before_check_out.write({'check_out': check_out_time})
                    hr_attendance.create({'employee_id': log.employee_id.id, 'check_in': log.punching_time,
                                          'punch_date': log.punching_time.date()})
            else:
                if log.status == '0':
                    att_id = self.check_in_check_out(log.employee_id.id,log.punching_time)
                    if not att_id:
                        hr_attendance.create({'employee_id': log.employee_id.id, 'check_in': log.punching_time})
                elif log.status == '1':
                    att_id = self.check_in_check_out(log.employee_id.id,log.punching_time)
                    if att_id:
                        attendance_id = hr_attendance.browse(att_id)
                        attendance_id.write({'check_out': log.punching_time})
                else:
                    att_id = self.check_in_check_out(log.employee_id.id,log.punching_time)
                    if att_id:
                        attendance_id = hr_attendance.browse(att_id)
                        attendance_id.write({'check_out': log.punching_time})
                    else:
                        hr_attendance.create({'employee_id': log.employee_id.id, 'check_in': log.punching_time})
            log.is_calculated = True

    def check_in_check_out(self, emp_id, time):
        attendances = self.env['hr.attendance'].search([('employee_id', '=', emp_id), ('check_out', '=', False)])
        if attendances:
            return attendances.id
