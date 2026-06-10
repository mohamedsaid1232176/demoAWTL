from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from math import floor


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    subscription_duration = fields.Integer(
        string="Subscription Period",
        compute="_compute_subscription_duration",
        readonly=True,
    )

    total_value = fields.Float(string="المبلغ المستحق")

    is_multi_product = fields.Boolean(string="Multiple Products", default=False)

    is_company_subscription = fields.Boolean(string="Is Subscription Company", related='company_id.is_subscription', readonly=True)

    building_product_id = fields.Many2one('product.template', string="مبنى",domain="[('unit_type','=','building')]")

    invoices_generated = fields.Boolean(string="Invoices Generated", default=False)

    main_contract_number = fields.Char(string="رقم سجل العقد الاساسي")
    contract_number = fields.Char(string="رقم سجل العقد")
    contract_type = fields.Many2one('contract.type', string="نوع العقد")
    contract_sealing_date = fields.Date(string="تاريخ ابرام العقد")
    contract_sealing_city = fields.Many2one('res.country.state', string="مكان ابرام العقد")

    organization_type = fields.Many2one('organization.type', string="نوع المنظمة")
    unified_number = fields.Char(string="الرقم الموحد")
    cr_date = fields.Date(string="تاريخ السجل التجاري")
    issued_by = fields.Char(string="جهة الإصدار")


    lessor_representative_id = fields.Many2one('lessor.representative', string="الممثل القانوني للمؤجر")
    nationality = fields.Char(string="الجنسية")
    nationality_type_id = fields.Many2one('nationality.type', string="نوع الهوية")
    mobile_number = fields.Char(string="رقم الجوال")
    email_address = fields.Char(string="البريد الإلكتروني")
    id_number_attachment = fields.Binary(string="صورة الهوية", attachment=True)
    id_number = fields.Char(string="رقم الهوية")


    tenancy_customer_id = fields.Many2one('res.partner', string="العميل المستأجر")
    tenancy_nationality = fields.Char(string="الجنسية")
    tenancy_id_type_id = fields.Many2one('nationality.type', string="نوع الهوية")
    tenancy_mobile_number = fields.Char(string="رقم الجوال")
    tenancy_email_address = fields.Char(string="البريد الإلكتروني")
    tenancy_id_number_attachment = fields.Binary(string="صورة الهوية", attachment=True)
    tenancy_id_number = fields.Char(string="رقم الهوية")

  
    broker_entity = fields.Many2one('broker.entity', string="المنشأة")

    brokerage_entity_name = fields.Char(
        related='broker_entity.brokerage_entity_name',
        string="اسم منشأة الوساطة العقارية",
        store=True
        ,readonly=False
    )

    brokerage_entity_address = fields.Char(
        related='broker_entity.brokerage_entity_address',
        string="عنوان منشأة الوساطة العقارية",
        store=True
        ,readonly=False
    )
    cr_entity_no = fields.Char(
        related='broker_entity.cr_entity_no',
        string="رقم السجل التجاري",
        store=True
        ,readonly=False
    )

    landline_number = fields.Char(
        related='broker_entity.landline_number',
        string="رقم الهاتف",
        store=True
        ,readonly=False
    )

    fax_number = fields.Char(
        related='broker_entity.fax_number',
        string="رقم الفاكس",
        store=True
        ,readonly=False
    )

    broker_name = fields.Char(
        related='broker_entity.broker_name',
        string="اسم الوظف",
        store=True
        ,readonly=False
    )

    broker_nationality = fields.Char(
        related='broker_entity.nationality',
        string="الجنسية",
        store=True
        ,readonly=False
    )

    broker_id_type_id = fields.Many2one(
        related='broker_entity.id_type_id',
        string="نوع الهوية",
        store=True
        ,readonly=False
    )

    broker_id_number = fields.Char(
        related='broker_entity.id_number',
        string="رقم الهوية",
        store=True
        ,readonly=False
    )

    broker_mobile_number = fields.Char(
        related='broker_entity.mobile_number',
        string="رقم الجوال",
        store=True
        ,readonly=False
    )

    broker_email_address = fields.Char(
        related='broker_entity.email_address',
        string="البريد الإلكتروني",
        store=True
        ,readonly=False
    )

    title_deed_no = fields.Char(string="رقم المستند")
    issuer = fields.Char(string="جهة الاصدار")
    issue_date = fields.Char(string="تاريخ الاصدار")
    place_of_issue = fields.Char(string="مكان الاصدار")
    title_deed_type = fields.Many2one('title.deed.type', string="نوع الصك")



    national_address = fields.Char(related='building_product_id.national_address',string="العنوان الوطني",readonly=False)
    location_description = fields.Char(related='building_product_id.location_description',string="وصف موقع العقار حسب الصك",readonly=False)
    property_usage = fields.Selection(related='building_product_id.property_usage',string ="الغرض من استخدام العقار",readonly=False)
    property_type = fields.Many2one(related='building_product_id.property_type',string="نوع بناء العقار",readonly=False)
    floor_no = fields.Char(related='building_product_id.floor_no',string="عدد الطوابق",readonly=False)
    elevators_no = fields.Char(related='building_product_id.elevators_no',string="عدد المصاعد",readonly=False)
    units_no = fields.Char(related='building_product_id.units_no',string="عدد الوحدات",readonly=False)
    parking_lots = fields.Char(related='building_product_id.parking_lots',string="عدد المواقف",readonly=False)


    unit_type = fields.Char(string="نوع الوحدة")
    floor_number = fields.Char(string="رقم الطابق")
    furnished =fields.Char(string="مؤثثة")
    ac_units = fields.Char(string="عدد وحدات التكييف")
    room_type = fields.Char(string="نوع الغرفة")
    electricity_meter_number = fields.Char(string="رقم عداد الكهرباء")
    gas_meter_number = fields.Char(string="رقم عداد الغاز")
    water_meter_number = fields.Char(string="رقم عداد المياة")
    unit_area = fields.Char(string="مساحة الوحدة")
    kitchen_cabinets = fields.Char(string="خزائن مطبخ مركبة ")
    furnishing_status = fields.Char(string="حالة التأثيث")
    numbers = fields.Char(string="العدد")
    current_meter_read_electricity = fields.Char(string="قراءة الكهرباء")
    current_meter_read_gas = fields.Char(string="قراءة الغاز")
    current_meter_read_water = fields.Char(string="قراءة المياه")

    @api.model
    def create(self, vals):
        if vals.get('partner_id') and not vals.get('tenancy_customer_id'):
            partner = self.env['res.partner'].browse(vals['partner_id'])

            # ✅ FIX هنا
            company_id = vals.get('company_id', self.env.company.id)
            company = self.env['res.company'].browse(company_id)

            vals.update({
                'organization_type': company.organization_type.id,
                'unified_number': company.unified_number,
                'cr_date': company.cr_date,
                'issued_by': company.issued_by,

                'tenancy_customer_id': partner.id,
                'tenancy_nationality': partner.tenancy_nationality,
                'tenancy_id_type_id': partner.tenancy_id_type_id.id,
                'tenancy_mobile_number': partner.mobile or partner.phone,
                'tenancy_email_address': partner.email,
                'tenancy_id_number': partner.tenancy_id,
            })

        return super().create(vals)


    def _recompute_subscription_products(self):

        for order in self:
            company = order.company_id

            company_states = company.subscription_state_ids.mapped('value')

            orders = self.search([
                ('company_id', '=', company.id),
                ('subscription_state', '!=', False),
            ])

            all_products = orders.mapped('order_line.product_id.product_tmpl_id')

            all_products.write({
                'subscription_product': False
            })

            active_orders = orders.filtered(
                lambda o: o.subscription_state in company_states
            )

            active_products = active_orders.mapped(
                'order_line.product_id.product_tmpl_id'
            )

            active_products.write({
                'subscription_product': True
            })

    def write(self, vals):
        res = super().write(vals)

        if 'subscription_state' in vals:
            self._recompute_subscription_products()

        return res
    
    
    @api.depends(
        'plan_id.billing_period_unit',
        'plan_id.billing_period_value',
        'start_date',
        'end_date'
    )
    def _compute_subscription_duration(self):
        for order in self:
            order.subscription_duration = 0

            if not (
                order.start_date
                and order.end_date
                and order.plan_id
                and order.plan_id.billing_period_unit
                and order.plan_id.billing_period_value
            ):
                continue

            if order.end_date < order.start_date:
                continue

            unit = order.plan_id.billing_period_unit
            value = order.plan_id.billing_period_value

            delta = relativedelta(
                order.end_date + relativedelta(days=1),
                order.start_date
            )

            if unit == 'week':
                total_units = delta.years * 52 + delta.months * 4 + delta.days // 7

            elif unit == 'month':
                total_units = delta.years * 12 + delta.months

            elif unit == 'year':
                total_units = delta.years

            else:
                total_units = 0

            order.subscription_duration = max(1, floor(total_units / value))

    def action_open_one_product_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'One Product Wizard',
            'res_model': 'one.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_quantity': 1,
                'default_sale_order_id': self.id,
                'building_product_id': self.building_product_id.id if self.building_product_id else False,

            }
        }
    def action_generate_one_product_invoices(self):
        self.ensure_one()

        if not self.order_line:
            raise UserError("Please add at least one product to the sale order.")

        if not self.subscription_duration:
            raise UserError("Subscription duration must be greater than zero.")

        invoices = []
        current_start_date = self.start_date
        invoice_currency = self.currency_id or self.company_id.currency_id

        if not invoice_currency:
            raise UserError("Please set a currency on the sale order or company before generating invoices.")

        unit = self.plan_id.billing_period_unit
        value = self.plan_id.billing_period_value
        sub_duration = int(self.subscription_duration)

        for i in range(sub_duration):
            if unit == 'week':
                current_end_date = current_start_date + relativedelta(weeks=value) - relativedelta(days=1)
            elif unit == 'month':
                current_end_date = current_start_date + relativedelta(months=value) - relativedelta(days=1)
            elif unit == 'year':
                current_end_date = current_start_date + relativedelta(years=value) - relativedelta(days=1)
            else:
                current_end_date = current_start_date

            invoice_lines = []

            if not self.is_multi_product:
                product_line = self.order_line[0]
                invoice_lines.append((0, 0, {
                    'product_id': product_line.product_id.id,
                    'quantity': 1,
                    'price_unit': product_line.price_unit,
                    'name': product_line.name,
                    'sale_line_ids': [(4, product_line.id)],
                    'deferred_start_date': current_start_date,
                    'deferred_end_date': current_end_date,
                    'product_uom_id': product_line.product_uom.id,
                }))
            else:
                for line in self.order_line:
                    invoice_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': 1,
                        'price_unit': line.price_unit,
                        'name': line.name,
                        'sale_line_ids': [(4, line.id)],
                        'deferred_start_date': current_start_date,
                        'deferred_end_date': current_end_date,
                        'product_uom_id': line.product_uom.id,
                    }))

            move = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.partner_id.id,
                'company_id': self.company_id.id,
                'currency_id': invoice_currency.id,
                'invoice_origin': self.name,
                'invoice_user_id': self.user_id.id,
                'invoice_date': current_start_date,
                'building_product_id': self.building_product_id.id,
                'invoice_line_ids': invoice_lines,
            })
            invoices.append(move.id)

            current_start_date = current_end_date + relativedelta(days=1)
        
        self.next_invoice_date = current_start_date
        
        for line in self.order_line:
            line.qty_delivered = sub_duration

        self.invoices_generated = True
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generated Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices)],
        }

    
    def action_open_multi_product_wizard(self):
        # company = self.env.company
        # company.write({'is_subscription': False})

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Multi Product Wizard',
            'res_model': 'multi.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'building_product_id': self.building_product_id.id if self.building_product_id else False,
            }
        }
   

    
