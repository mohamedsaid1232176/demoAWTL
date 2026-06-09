import logging

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    spl_search_text = fields.Char(string='SPL Search Text')
    spl_building_number = fields.Char(string='Building Number')
    spl_additional_number = fields.Char(string='Additional Number')
    spl_postcode = fields.Char(string='Post Code')
    spl_district = fields.Char(string='District')
    spl_region_name = fields.Char(string='Region')
    spl_latitude = fields.Float(string='Latitude', digits=(16, 10))
    spl_longitude = fields.Float(string='Longitude', digits=(16, 10))
    spl_address_verified = fields.Boolean(string='SPL Verified', readonly=True)
    spl_status_description = fields.Char(string='SPL Status', readonly=True)

    def action_spl_search_address(self):
        for partner in self:
            partner._spl_search_address()
        return True

    def action_spl_verify_address(self):
        for partner in self:
            partner._spl_verify_address()
        return True

    def _spl_get_config(self):
        params = self.env['ir.config_parameter'].sudo()
        api_key = params.get_param('spl_national_address.api_key')
        base_url = params.get_param(
            'spl_national_address.base_url',
            'https://apina.address.gov.sa/NationalAddress',
        )
        if not api_key:
            raise UserError(_('Please configure the SPL National Address API key in Settings.'))
        return base_url.rstrip('/'), api_key

    def _spl_request(self, endpoint, query):
        base_url, api_key = self._spl_get_config()
        query = {
            'language': 'A',
            'format': 'JSON',
            'encode': 'utf8',
            **query,
            'api_key': api_key,
        }
        try:
            response = requests.get(
                f'{base_url}/{endpoint.lstrip("/")}',
                params=query,
                timeout=20,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            _logger.exception('SPL National Address request failed')
            raise UserError(_('SPL request failed: %s') % error) from error
        except ValueError as error:
            raise UserError(_('SPL returned an invalid JSON response.')) from error

    def _spl_search_address(self):
        self.ensure_one()
        search_text = self.spl_search_text or self.contact_address or self.name
        if not search_text:
            raise UserError(_('Please enter SPL Search Text first.'))

        result = self._spl_request(
            'v4/address/address-free-text',
            {
                'page': 1,
                'addressstring': search_text,
            },
        )
        self.spl_status_description = result.get('statusdescription')
        addresses = result.get('Addresses') or []
        if not result.get('success') or not addresses:
            self.spl_address_verified = False
            raise UserError(_('No SPL National Address was found for this search.'))

        self._spl_apply_address(addresses[0])

    def _spl_verify_address(self):
        self.ensure_one()
        missing_fields = []
        if not self.spl_building_number:
            missing_fields.append(_('Building Number'))
        if not self.spl_additional_number:
            missing_fields.append(_('Additional Number'))
        if not self.spl_postcode:
            missing_fields.append(_('Post Code'))
        if missing_fields:
            raise UserError(_('Please fill: %s') % ', '.join(missing_fields))

        result = self._spl_request(
            'v3.1/address/address-verify',
            {
                'page': 1,
                'Buildingnumber': self.spl_building_number,
                'Additionalnumber': self.spl_additional_number,
                'Zipcode': self.spl_postcode,
            },
        )
        self.write({
            'spl_address_verified': bool(result.get('addressfound')),
            'spl_status_description': result.get('statusdescription') or (
                _('Address found') if result.get('addressfound') else _('Address not found')
            ),
        })

    def _spl_apply_address(self, address):
        obj_lat_lng = (address.get('ObjLatLng') or '').split()
        longitude = latitude = 0.0
        if len(obj_lat_lng) >= 3:
            try:
                longitude = float(obj_lat_lng[1])
                latitude = float(obj_lat_lng[2])
            except ValueError:
                longitude = latitude = 0.0

        vals = {
            'street': address.get('Street') or self.street,
            'street2': address.get('District') or self.street2,
            'city': address.get('City') or self.city,
            'zip': address.get('PostCode') or self.zip,
            'spl_building_number': address.get('BuildingNumber'),
            'spl_additional_number': address.get('AdditionalNumber'),
            'spl_postcode': address.get('PostCode'),
            'spl_district': address.get('District'),
            'spl_region_name': address.get('RegionName'),
            'spl_latitude': latitude,
            'spl_longitude': longitude,
            'spl_address_verified': True,
            'spl_status_description': _('Address loaded from SPL'),
        }
        self.write(vals)
