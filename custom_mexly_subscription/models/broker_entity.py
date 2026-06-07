from odoo import models, fields, api


class BrokerEntity(models.Model):
    _name = 'broker.entity'
    _description = 'Broker Entity'
    _rec_name = 'brokerage_entity_name'

    brokerage_entity_name = fields.Char(string="اسم منشأة الوساطة العقارية")

    brokerage_entity_address = fields.Char(string="عنوان منشأة الوساطة العقارية")
    cr_entity_no = fields.Char(string="رقم السجل التجاري")
    landline_number = fields.Char(string="رقم الهاتف")
    fax_number = fields.Char(string="رقم الفاكس")
    broker_name = fields.Char(string="اسم الموظف")
    nationality = fields.Char(string="الجنسية")
    id_type_id = fields.Many2one('nationality.type', string="نوع الهوية")
    id_number = fields.Char(string="رقم الهوية")
    id_number_attachment = fields.Binary(string="صورة الهوية", attachment=True)
    mobile_number = fields.Char(string="رقم الجوال")
    email_address = fields.Char(string="البريد الإلكتروني")