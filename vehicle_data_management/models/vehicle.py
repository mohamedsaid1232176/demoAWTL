import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class VehicleData(models.Model):
    _name = "vehicledata"
    _description = "Vehicle Data"
    _rec_name = "name"  # title displayed


    # Sequence field (title)
    name = fields.Char(string="Equipment ID", readonly=True, default="New")

    vehicle_number = fields.Char(string="Vehicle Number")
    arabic_vehicle_number = fields.Char(string="Arabic Vehicle Number")

    # ✅ REQUIRED
    vehicle_name = fields.Char(string="Vehicle Name", required=True)

    # ✅ REQUIRED
    company_id = fields.Many2one(
        "res.partner",
        string="Company",
        # required=True
    )

    username = fields.Char(string="Username")
    password = fields.Char(string="Password")
    driver = fields.Char(string="Driver")

    # ✅ REQUIRED
    device_type_id = fields.Many2one(
        "device.type",
        string="Device Type",
        required=True
    )

    # ✅ REQUIRED
    imei = fields.Char(string="IMEI", required=True)

    # ✅ REQUIRED
    sim_no = fields.Char(string="Sim No", required=True)

    install_date = fields.Date(string="Install Date")

    # ✅ REQUIRED
    installation_type_id = fields.Many2one(
        "installation.type",
        string="Installation Type",
        required=True
    )

    expiry_date = fields.Date(string="Expiry Date")

    # ✅ REQUIRED
    status = fields.Selection([
        ("active", "Active"),
        ("not_active", "Not Active"),
    ], string="Status", required=True)

    installer = fields.Char(string="Installer")

    # ✅ REQUIRED
    installed_location_id = fields.Many2one(
        'res.country.state',
        string='Installed Location',
        domain="[('country_id.code', '=', 'SA')]",
        required=True
    )

    base_location = fields.Char(string="Base Location")

    # ✅ REQUIRED
    vehicle_type_id = fields.Many2one(
        "vehicle.type",
        string="Vehicle Type",
        required=True
    )

    brand = fields.Char(string="Brand")
    driver_mobile_no = fields.Char(string="Driver Mobile No")
    location = fields.Char(string="Location")
    renewed_at = fields.Date(string="Renewed At")

    @api.model
    def create(self, vals):
        """Auto-generate sequence when creating record"""
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("equipment.seq") or "New"
        return super().create(vals)

    @api.constrains("driver_mobile_no")
    def _check_mobile_format(self):
        for rec in self:
            if rec.driver_mobile_no:
                # Regex: يبدأ بـ + اختياري ثم أرقام فقط
                pattern = r"^\+?\d+$"
                if not re.match(pattern, rec.driver_mobile_no):
                    raise ValidationError(
                        "Driver Mobile must contain only digits and optionally start with '+'."
                    )



class DeviceType(models.Model):
    _name = "device.type"
    _description = "Device Type"

    name = fields.Char(string="Device Type", required=True)



class InstallationType(models.Model):
    _name = "installation.type"
    _description = "Installation Type"

    name = fields.Char(string="Installation Type", required=True)


class VehicleType(models.Model):
    _name = "vehicle.type"
    _description = "Vehicle Type"

    name = fields.Char(string="Vehicle Type", required=True)
