from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    spl_national_address_api_key = fields.Char(
        string='SPL National Address API Key',
        config_parameter='spl_national_address.api_key',
    )
    spl_national_address_base_url = fields.Char(
        string='SPL National Address Base URL',
        config_parameter='spl_national_address.base_url',
        default='https://apina.address.gov.sa/NationalAddress',
    )
