from odoo import models, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains(
        'company_type',
        'country_id',
        'street',
        'street2',
        'city',
        'state_id',
        'zip',
        'l10n_sa_edi_building_number',
        'l10n_sa_edi_plot_identification',
    )
    def _check_sa_required_fields(self):
        for rec in self:
            # الشرط الأساسي
            if rec.company_type == 'company' and rec.country_id and rec.country_id.code == 'SA':
                missing_fields = []

                # العنوان الوطني الأساسي
                if not rec.street:
                    missing_fields.append("Street")
                if not rec.street2:
                    missing_fields.append("District")
                if not rec.city:
                    missing_fields.append("City")
                if not rec.state_id:
                    missing_fields.append("State")
                if not rec.zip:
                    missing_fields.append("ZIP")

                # Building Number
                if not rec.l10n_sa_edi_building_number:
                    missing_fields.append("Building Number")

                # Plot Identification
                if not rec.l10n_sa_edi_plot_identification:
                    missing_fields.append("Plot Identification")

                if missing_fields:
                    raise ValidationError(
                        "يجب إدخال بيانات العنوان الوطني بالكامل للشركات داخل السعودية.\n"
                        f"الحقول الناقصة: {', '.join(missing_fields)}"
                    )
