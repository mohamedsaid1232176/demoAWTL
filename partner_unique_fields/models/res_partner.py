from odoo import models, api,fields
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    tax_id = fields.Char(
        string="Tax ID",
        copy=False,
        required=1,
        index=True
    )
    _sql_constraints = [
        ('unique_vat_company', 'unique(vat, company_id)', 'VAT Number must be unique per company!'),
        ('unique_phone', 'unique(phone)', 'Phone must be unique!'),
        ('unique_mobile', 'unique(mobile)', 'Mobile must be unique!'),
        ('unique_name_company', 'unique(name, company_id)', 'Name must be unique per company!'),
    ]

    @api.constrains('vat', 'tax_id', 'phone', 'mobile', 'name')
    def _check_unique_fields(self):
        for rec in self:
            if rec.vat and self.search_count([
                ('vat', '=', rec.vat),
                ('company_id', '=', rec.company_id.id),
                ('id', '!=', rec.id)
            ]):
                raise ValidationError("VAT Number already exists!")

            if rec.tax_id and self.search_count([
                ('tax_id', '=', rec.tax_id),
                ('id', '!=', rec.id)
            ]):
                raise ValidationError("Tax ID already exists!")

            if rec.phone and self.search_count([
                ('phone', '=', rec.phone),
                ('id', '!=', rec.id)
            ]):
                raise ValidationError("Phone already exists!")

            if rec.mobile and self.search_count([
                ('mobile', '=', rec.mobile),
                ('id', '!=', rec.id)
            ]):
                raise ValidationError("Mobile already exists!")

            if rec.name and self.search_count([
                ('name', '=', rec.name),
                ('company_id', '=', rec.company_id.id),
                ('id', '!=', rec.id)
            ]):
                raise ValidationError("Name already exists!")
