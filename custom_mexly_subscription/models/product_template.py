from itertools import product

from odoo import models, fields, api
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
    
    )
    
    is_company_subscription = fields.Boolean(string="Is Subscription Company", compute='_compute_is_company_subscription', readonly=True)

    subscription_product = fields.Boolean(string='Subscription Product', default=False)


    building_id = fields.Many2one( 'product.template',string="مبنى", domain="[('unit_type', '=', 'building')]")

    apartment_id = fields.Many2one('product.template', string="شقة", domain="[('unit_type', '=', 'apartment')]")

    room_id = fields.Many2one('product.template', string="غرفة", domain="[('unit_type', '=', 'room')]")

    unit_type = fields.Selection(
        [('apartment', 'شقة'), ('building', 'مبنى'), ('room', 'غرفة'),('bed','سرير'),('service','خادمي')],
        string="Unit Type"
    )

    national_address = fields.Char(string="العنوان الوطني")
    location_description = fields.Char(string="وصف موقع العقار حسب الصك")
    property_usage = fields.Selection([('residential', 'سكني'), ('commercial', 'تجاري')] ,string ="الغرض من استخدام العقار")
    property_type = fields.Many2one( 'property.type',string="نوع بناء العقار")
    floor_no = fields.Char(string="عدد الطوابق")
    elevators_no = fields.Char(string="عدد المصاعد")
    units_no = fields.Char(string="عدد الوحدات")
    parking_lots = fields.Char(string="عدد المواقف")



    @api.depends('company_id')
    def _compute_is_company_subscription(self):
        for product in self:
            product.is_company_subscription = product.company_id.is_subscription

    def action_link_analytic(self):
        self.ensure_one()

        if not self.analytic_account_id:
            raise UserError("Please select an Analytic Account first.")

        analytic = self.analytic_account_id

        if not self.unit_type:
            raise UserError("Product must have a Unit Type.")

        if not analytic.unit_type:
            analytic.unit_type = self.unit_type

      
        if self.unit_type == 'building':
            return

     
        elif self.unit_type == 'apartment':
            if not self.building_id:
                raise UserError("Apartment must have a building.")

            building_analytic = self.building_id.analytic_account_id

            if not building_analytic:
                raise UserError("Building must have analytic account.")

            analytic.write({
                'building_id': self.building_id.id
            })

            building_analytic.write({
                'apartment_ids': [(4, self.id)],
            })

       
        elif self.unit_type == 'room':
            if not self.building_id or not self.apartment_id:
                raise UserError("Room must have building and apartment.")

            building_analytic = self.building_id.analytic_account_id
            apartment_analytic = self.apartment_id.analytic_account_id

            if not building_analytic or not apartment_analytic:
                raise UserError("Missing analytic accounts.")

            analytic.write({
                'building_id': self.building_id.id,
                'apartment_id': self.apartment_id.id,
            })

            apartment_analytic.write({
                'room_ids': [(4, self.id)],
            })

            building_analytic.write({
                'room_ids': [(4, self.id)],
            })

        elif self.unit_type == 'bed':
            if not self.building_id or not self.apartment_id or not self.room_id:
                raise UserError("Bed must have full hierarchy.")

            building_analytic = self.building_id.analytic_account_id
            apartment_analytic = self.apartment_id.analytic_account_id
            room_analytic = self.room_id.analytic_account_id

            if not all([building_analytic, apartment_analytic, room_analytic]):
                raise UserError("Missing analytic accounts.")

            analytic.write({
                'building_id': self.building_id.id,
                'apartment_id': self.apartment_id.id,
                'room_id': self.room_id.id,
            })

            room_analytic.write({
                'bed_ids': [(4, self.id)]
            })

            apartment_analytic.write({
                'bed_ids': [(4, self.id)]
            })

            building_analytic.write({
                'bed_ids': [(4, self.id)]
            })

    @api.model
    def create(self, vals):
        product = super().create(vals)

        company = product.company_id or self.env.company

        if company.is_subscription:

            plan = self.env['account.analytic.plan'].search([], limit=1)

            if not plan:
                raise UserError("Please configure at least one Analytic Plan.")

            # if not product.unit_type:
            #     raise UserError("Please select Unit Type before creating this product.")

            if product.unit_type == 'building':
                analytic_vals = {
                    'name': product.name,
                    'company_id': company.id,
                    'plan_id': plan.id,
                    'product_id': product.id,
                }
                analytic_account = self.env['account.analytic.account'].create(analytic_vals)
                product.analytic_account_id = analytic_account.id

            elif product.unit_type == 'apartment':
                if not product.building_id:
                    raise UserError("Please select a building for this apartment.")

                building_analytic = product.building_id.analytic_account_id
                if not building_analytic:
                    building_vals = {
                        'name': product.building_id.name,
                        'company_id': company.id,
                        'plan_id': plan.id,
                        'product_id': product.building_id.id,
                    }
                    building_analytic = self.env['account.analytic.account'].create(building_vals)
                    product.building_id.analytic_account_id = building_analytic.id

                building_analytic.write({
                    'apartment_ids': [(4, product.id)]
                })

                analytic_vals = {
                    'name': product.name,
                    'company_id': company.id,
                    'plan_id': plan.id,
                    'product_id': product.id,
                    'building_id': product.building_id.id,
                }
                analytic_account = self.env['account.analytic.account'].create(analytic_vals)
                product.analytic_account_id = analytic_account.id

            elif product.unit_type == 'room':
                if not product.building_id or not product.apartment_id:
                    raise UserError("Please select building and apartment for this room.")

                apartment_analytic = product.apartment_id.analytic_account_id
                if not apartment_analytic:
                    raise UserError("The apartment must have an analytic account before adding a room.")
                
                building_analytic = product.building_id.analytic_account_id

                if not building_analytic :
                    raise UserError("The building must have an analytic account before adding a room.")
                

                apartment_analytic.write({
                    'room_ids': [(4, product.id)]
                })

                building_analytic.write({
                    'room_ids': [(4, product.id)]

                })
                    
               
                building_analytic.write({
                    'apartment_ids': [(4, product.apartment_id.id)]
                })



                analytic_vals = {
                    'name': product.name,
                    'company_id': company.id,
                    'plan_id': plan.id,
                    'product_id': product.id,
                    'building_id': product.building_id.id,
                    'apartment_id': product.apartment_id.id,
                }
                analytic_account = self.env['account.analytic.account'].create(analytic_vals)
                product.analytic_account_id = analytic_account.id
            
            elif product.unit_type == 'bed':
                if not product.building_id or not product.apartment_id or not product.room_id:
                    raise UserError("Please select building, apartment and room for this bed.")

                room_analytic = product.room_id.analytic_account_id
                if not room_analytic:
                    raise UserError("The room must have an analytic account before adding a bed.")

                apartment_analytic = product.apartment_id.analytic_account_id
                if not apartment_analytic:
                    raise UserError("The apartment must have an analytic account before adding a bed.")

                building_analytic = product.building_id.analytic_account_id
                if not building_analytic:
                    raise UserError("The building must have an analytic account before adding a bed.")

                room_analytic.write({
                    'bed_ids': [(4, product.id)]
                })

                apartment_analytic.write({
                    'bed_ids': [(4, product.id)]
                })

                building_analytic.write({
                    'bed_ids': [(4, product.id)]
                })

                analytic_vals = {
                    'name': product.name,
                    'company_id': company.id,
                    'plan_id': plan.id,
                    'product_id': product.id,
                    'building_id': product.building_id.id,
                    'apartment_id': product.apartment_id.id,
                    'room_id': product.room_id.id,
                }

                analytic_account = self.env['account.analytic.account'].create(analytic_vals)
                product.analytic_account_id = analytic_account.id

        return product
    
    def write(self, vals):
        old_values = {
            product.id: {
                'building': product.building_id,
                'apartment': product.apartment_id,
                'room': product.room_id,
            }
            for product in self
        }

        res = super().write(vals)

        for product in self:
            old_value = old_values[product.id]
            old_building = old_value['building']
            old_apartment = old_value['apartment']
            old_room = old_value['room']

            company = product.company_id or self.env.company
            if not company.is_subscription:
                continue

            if product.unit_type == 'apartment':
                if old_building and old_building != product.building_id:
                    old_building_analytic = old_building.analytic_account_id
                    if old_building_analytic:
                        old_building_analytic.write({
                            'apartment_ids': [(3, product.id)]
                        })

                if product.building_id:
                    new_building_analytic = product.building_id.analytic_account_id
                    if new_building_analytic:
                        new_building_analytic.write({
                            'apartment_ids': [(4, product.id)]
                        })

            elif product.unit_type == 'room':
                if old_apartment and old_apartment != product.apartment_id:
                    old_apartment_analytic = old_apartment.analytic_account_id
                    if old_apartment_analytic:
                        old_apartment_analytic.write({
                            'room_ids': [(3, product.id)]
                        })

                if product.apartment_id:
                    new_apartment_analytic = product.apartment_id.analytic_account_id
                    if new_apartment_analytic:
                        new_apartment_analytic.write({
                            'room_ids': [(4, product.id)]
                        })

                if old_building and old_building != product.building_id:
                    old_building_analytic = old_building.analytic_account_id
                    if old_building_analytic:
                        old_building_analytic.write({
                            'room_ids': [(3, product.id)]
                        })

                if product.building_id:
                    new_building_analytic = product.building_id.analytic_account_id
                    if new_building_analytic:
                        new_building_analytic.write({
                            'room_ids': [(4, product.id)]
                        })

            elif product.unit_type == 'bed':
                if old_room and old_room != product.room_id:
                    old_room_analytic = old_room.analytic_account_id
                    if old_room_analytic:
                        old_room_analytic.write({
                            'bed_ids': [(3, product.id)]
                        })

                if product.room_id:
                    new_room_analytic = product.room_id.analytic_account_id
                    if new_room_analytic:
                        new_room_analytic.write({
                            'bed_ids': [(4, product.id)]
                        })

                if old_apartment and old_apartment != product.apartment_id:
                    old_apartment_analytic = old_apartment.analytic_account_id
                    if old_apartment_analytic:
                        old_apartment_analytic.write({
                            'bed_ids': [(3, product.id)]
                        })

                if product.apartment_id:
                    new_apartment_analytic = product.apartment_id.analytic_account_id
                    if new_apartment_analytic:
                        new_apartment_analytic.write({
                            'bed_ids': [(4, product.id)]
                        })

                if old_building and old_building != product.building_id:
                    old_building_analytic = old_building.analytic_account_id
                    if old_building_analytic:
                        old_building_analytic.write({
                            'bed_ids': [(3, product.id)]
                        })

                if product.building_id:
                    new_building_analytic = product.building_id.analytic_account_id
                    if new_building_analytic:
                        new_building_analytic.write({
                            'bed_ids': [(4, product.id)]
                        })

        return res
