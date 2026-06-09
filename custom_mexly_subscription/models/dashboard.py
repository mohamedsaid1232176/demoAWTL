# -*- coding: utf-8 -*-
from odoo import models, fields, api
import re

from datetime import datetime

from odoo.exceptions import ValidationError


# =========================
# DASHBOARD MAIN (زي ما هو)
# =========================
class SubscriptionDashboard(models.TransientModel):
    _name = 'subscription.dashboard'
    _description = 'Dashboard'
    name = fields.Char(default="Dashboard")
    building_id = fields.Many2one(
        'product.template',
        string="Building",
        domain=[('unit_type', '=', 'building')]
    )
    total_revenue = fields.Float(
        string="Total Revenue",
        compute="_compute_total_revenue"
    )

    @api.depends(
        'apartment_revenue',
        'building_revenue',
        'room_revenue',
        'bed_revenue',
        'service_revenue'
    )
    def _compute_total_revenue(self):
        for rec in self:
            rec.total_revenue = (
                    rec.apartment_revenue +
                    rec.building_revenue +
                    rec.room_revenue +
                    rec.bed_revenue +
                    rec.service_revenue
            )

    def action_analyze_building(self):
        self.ensure_one()

        if not self.building_id:
            raise ValidationError("لازم تختار المبنى الأول")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Building Invoice Analysis',

            # 🔥 أهم تغيير
            'res_model': 'account.invoice.report',

            # 🔥 خليها pivot + list
            'view_mode': 'list',

            'target': 'new',  # أو new لو popup

            'domain': [
                ('move_type', '=', 'out_invoice'),
                ('payment_state', 'in', ['not_paid', 'partial']),

                ('product_id.product_tmpl_id.building_id', '=', self.building_id.id)
            ],

            'context': {
                # 🔥 measure
                'pivot_measures': ['price_subtotal'],

                # 🔥 grouping
                'group_by': ['product_id'],
            }
        }
    apartment_count = fields.Integer(compute="_compute_counts")
    building_count = fields.Integer(compute="_compute_counts")
    room_count = fields.Integer(compute="_compute_counts")
    bed_count = fields.Integer(compute="_compute_counts")
    service_count = fields.Integer(compute="_compute_counts")

    apartment_sales = fields.Float(compute="_compute_totals")
    apartment_cost = fields.Float(compute="_compute_totals")

    building_sales = fields.Float(compute="_compute_totals")
    building_cost = fields.Float(compute="_compute_totals")

    room_sales = fields.Float(compute="_compute_totals")
    room_cost = fields.Float(compute="_compute_totals")

    bed_sales = fields.Float(compute="_compute_totals")
    bed_cost = fields.Float(compute="_compute_totals")

    service_sales = fields.Float(compute="_compute_totals")
    service_cost = fields.Float(compute="_compute_totals")

    apartment_revenue = fields.Float(compute="_compute_totals")
    building_revenue = fields.Float(compute="_compute_totals")
    room_revenue = fields.Float(compute="_compute_totals")
    bed_revenue = fields.Float(compute="_compute_totals")
    service_revenue = fields.Float(compute="_compute_totals")

    subscription_states = fields.Many2many(
        'subscription.state.helper',
        string="Subscription Status"
    )

    unused_apartment_count = fields.Integer(compute="_compute_unused")
    unused_building_count = fields.Integer(compute="_compute_unused")
    unused_room_count = fields.Integer(compute="_compute_unused")
    unused_bed_count = fields.Integer(compute="_compute_unused")
    unused_service_count = fields.Integer(compute="_compute_unused")

    unused_apartment_sales = fields.Float(compute="_compute_unused_totals")
    unused_apartment_cost = fields.Float(compute="_compute_unused_totals")

    unused_building_sales = fields.Float(compute="_compute_unused_totals")
    unused_building_cost = fields.Float(compute="_compute_unused_totals")

    unused_room_sales = fields.Float(compute="_compute_unused_totals")
    unused_room_cost = fields.Float(compute="_compute_unused_totals")

    unused_bed_sales = fields.Float(compute="_compute_unused_totals")
    unused_bed_cost = fields.Float(compute="_compute_unused_totals")

    unused_service_sales = fields.Float(compute="_compute_unused_totals")
    unused_service_cost = fields.Float(compute="_compute_unused_totals")

    def open_invoices_to_pay_pivot(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices To Pay',
            'res_model': 'account.move',
            'view_mode': 'pivot',
            'target': 'new',

            # 🔥 الفلتر (To Pay)
            'domain': [
                ('move_type', '=', 'out_invoice'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ],

            # 🔥 الكونتكست (group + measure)
            'context': {
                # ✅ الفلتر الصح
                'search_default_open': 1,

                # ✅ يجيب invoices بس
                'search_default_out_invoice': 1,

                # ✅ grouping
                # 'search_default_partner': 1,

                'pivot_measures': ['amount_residual'],  # Amount Due
                'group_by': ['partner_id'],  # Partner
            }
        }

    def open_aged_receivable(self):
        action = self.env.ref('account_reports.action_account_report_ar').read()[0]
        action['target'] = 'new'  # 🔥 أهم سطر
        return action

    def _compute_unused_totals(self):
        Product = self.env['product.template']
        SaleLine = self.env['sale.order.line']

        for rec in self:
            def calc(unit):
                all_products = Product.search([
                    ('unit_type', '=', unit)
                ])

                # ✅ exclude churned
                used_products = SaleLine.search([
                    ('product_id.product_tmpl_id.unit_type', '=', unit),
                    ('order_id.subscription_state', '!=', '6_churn')
                ]).mapped('product_id.product_tmpl_id')

                unused = all_products - used_products

                sales = sum(unused.mapped('list_price'))
                cost = sum(unused.mapped('standard_price'))

                return sales, cost

            rec.unused_apartment_sales, rec.unused_apartment_cost = calc('apartment')
            rec.unused_building_sales, rec.unused_building_cost = calc('building')
            rec.unused_room_sales, rec.unused_room_cost = calc('room')
            rec.unused_bed_sales, rec.unused_bed_cost = calc('bed')
            rec.unused_service_sales, rec.unused_service_cost = calc('service')

    def _compute_unused(self):
        SaleLine = self.env['sale.order.line']
        Product = self.env['product.template']

        for rec in self:
            def get_unused(unit):
                all_products = Product.search([
                    ('unit_type', '=', unit)
                ])

                # ✅ نجيب بس المنتجات اللي حالتها مش churned
                used_products = SaleLine.search([
                    ('product_id.product_tmpl_id.unit_type', '=', unit),
                    ('order_id.subscription_state', '!=', '6_churn')  # 🔥 المهم
                ]).mapped('product_id.product_tmpl_id')

                unused = all_products - used_products

                return len(unused)

            rec.unused_apartment_count = get_unused('apartment')
            rec.unused_building_count = get_unused('building')
            rec.unused_room_count = get_unused('room')
            rec.unused_bed_count = get_unused('bed')
            rec.unused_service_count = get_unused('service')

    def open_unused_products(self):
        self.ensure_one()

        unit_type = self.env.context.get('unit_type')

        Product = self.env['product.template']
        SaleLine = self.env['sale.order.line']

        # كل المنتجات
        all_products = Product.search([
            ('unit_type', '=', unit_type)
        ])

        # المستخدمة
        used_products = SaleLine.search([
            ('product_id.product_tmpl_id.unit_type', '=', unit_type),
            ('order_id.subscription_state', '!=', '6_churn')  # 🔥 مهم جدا
        ]).mapped('product_id.product_tmpl_id')
        # غير المستخدمة
        unused_products = all_products - used_products

        # 🔥 نعمل dashboard جديد
        dashboard = self.env['product.list.dashboard'].create({
            'unit_type': unit_type
        })

        # 🔥 نضيف المنتجات يدوي
        total_sales = 0
        total_cost = 0

        SaleLine = self.env['sale.order.line']

        for p in unused_products:
            lines = SaleLine.search([
                ('product_id.product_tmpl_id', '=', p.id),
                ('order_id.subscription_state', '!=', '6_churn')  # نفس اللوجيك
            ])

            revenue = sum(lines.mapped('price_subtotal'))

            self.env['product.list.line'].create({
                'dashboard_id': dashboard.id,
                'product_id': p.id,
                'name': p.name,
                'list_price': p.list_price,
                'standard_price': p.standard_price,
                'total_revenue': revenue,  # 🔥 NEW
            })

            total_sales += p.list_price
            total_cost += p.standard_price

        dashboard.total_sales = total_sales
        dashboard.total_cost = total_cost

        return {
            'type': 'ir.actions.act_window',
            'name': 'Unused Products Dashboard',
            'res_model': 'product.list.dashboard',
            'view_mode': 'form',
            'res_id': dashboard.id,
            'target': 'new',  # 🔥 popup زي الصورة
        }

    def action_apply_filter(self):
        self.ensure_one()

        # 🔥 احفظ الحالات المختارة في record
        self.write({
            'subscription_states': [(6, 0, self.subscription_states.ids)]
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Dashboard',
            'res_model': 'subscription.dashboard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def open_graph(self):
        self.ensure_one()

        # 🧹 امسح القديم
        self.env['dashboard.graph'].search([]).unlink()

        # 🔥 data من الداشبورد
        data = [
            ('Apartment', self.apartment_sales),
            ('Building', self.building_sales),
            ('Room', self.room_sales),
            ('Bed', self.bed_sales),
            ('Service', self.service_sales),
        ]

        for name, value in data:
            self.env['dashboard.graph'].create({
                'name': name,
                'value': value
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Dashboard Graph',
            'res_model': 'dashboard.graph',
            'view_mode': 'graph',
            'target': 'new',
        }

    # 🔥 ADD: يمنع تكرار الداشبورد
    @api.model
    def create(self, vals):
        existing = self.search([], limit=1)
        if existing:
            return existing
        return super().create(vals)

    # 🔥 ADD: يفتح نفس الداشبورد كل مرة
    def action_open_dashboard(self):
        dashboard = self.search([], limit=1)

        if not dashboard:
            dashboard = self.create({})

        return {
            'type': 'ir.actions.act_window',
            'name': 'Dashboard',
            'res_model': 'subscription.dashboard',
            'view_mode': 'form',
            'res_id': dashboard.id,
        }

    def _compute_counts(self):
        SaleLine = self.env['sale.order.line']

        for rec in self:
            states = rec.subscription_states.mapped('code')

            def count(unit):
                if states:
                    domain = [
                        ('product_id.product_tmpl_id.unit_type', '=', unit),
                        ('order_id.subscription_state', 'in', states)
                    ]

                    lines = SaleLine.search(domain)

                    # ✅ عد المنتجات unique
                    products = lines.mapped('product_id.product_tmpl_id')
                    return len(set(products.ids))

                else:
                    return self.env['product.template'].search_count([
                        ('unit_type', '=', unit)
                    ])

            rec.apartment_count = count('apartment')
            rec.building_count = count('building')
            rec.room_count = count('room')
            rec.bed_count = count('bed')
            rec.service_count = count('service')

    def _compute_totals(self):
        SaleLine = self.env['sale.order.line']
        Product = self.env['product.template']

        for rec in self:
            def calc(unit):
                states = rec.subscription_states.mapped('code')

                # ✅ لو فيه filter → اشتغل على sale lines
                if states:
                    domain = [
                        ('product_id.product_tmpl_id.unit_type', '=', unit),
                        ('order_id.subscription_state', 'in', states)
                    ]

                    lines = SaleLine.search(domain)

                    sales = sum(lines.mapped('price_unit'))
                    cost = sum(lines.mapped('product_id.standard_price'))
                    revenue = sum(lines.mapped('price_subtotal'))

                # ✅ لو مفيش filter → هات كل المنتجات من السيستم
                else:
                    products = Product.search([
                        ('unit_type', '=', unit)
                    ])

                    lines = SaleLine.search([
                        ('product_id.product_tmpl_id.unit_type', '=', unit)
                    ])

                    sales = sum(products.mapped('list_price'))
                    cost = sum(products.mapped('standard_price'))
                    revenue = sum(lines.mapped('price_subtotal'))  # ✅ الصح
                return sales, cost, revenue

            rec.apartment_sales, rec.apartment_cost, rec.apartment_revenue = calc('apartment')
            rec.building_sales, rec.building_cost, rec.building_revenue = calc('building')
            rec.room_sales, rec.room_cost, rec.room_revenue = calc('room')
            rec.bed_sales, rec.bed_cost, rec.bed_revenue = calc('bed')
            rec.service_sales, rec.service_cost, rec.service_revenue = calc('service')


    # 🔥 فتح الداشبورد الجديد
    def open_products(self):
        self.ensure_one()

        unit_type = self.env.context.get('unit_type')

        # ✅ خد states زي ما هي
        states = self.subscription_states.mapped('code')

        print("FIXED STATES =", states)

        dashboard = self.env['product.list.dashboard'].create_dashboard(unit_type, states)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Products Dashboard',
            'res_model': 'product.list.dashboard',
            'view_mode': 'form',
            'res_id': dashboard.id,
            'target': 'new',
            'context': {
                'states': states  # 🔥 أهم سطر
            }
        }


# =========================
# PRODUCT DASHBOARD LINE (زي ما هو)
# =========================
class ProductDashboardLine(models.TransientModel):
    _name = 'product.dashboard.line'

    viewer_id = fields.Many2one('product.dashboard.viewer')
    order_id = fields.Many2one('sale.order')
    unit_price = fields.Float()
    subtotal = fields.Float()

    # ✅ الجديد
    start_date = fields.Date()
    end_date = fields.Date()


# =========================
# PRODUCT DETAILS VIEWER (زي ما هو)
# =========================
class ProductDashboardViewer(models.TransientModel):
    _name = 'product.dashboard.viewer'

    product_id = fields.Many2one('product.template')

    line_ids = fields.One2many(
        'product.dashboard.line',
        'viewer_id'
    )

    total_unit_price = fields.Float()
    total_revenue = fields.Float()
    total_amount = fields.Float()
    line_count = fields.Integer()

    def sort_by_unit_price(self):
        self.ensure_one()

        sorted_lines = self.line_ids.sorted(
            key=lambda l: l.unit_price,
            reverse=True
        )

        self.line_ids = [(5, 0, 0)] + [
            (0, 0, {
                'order_id': l.order_id.id,
                'unit_price': l.unit_price,
                'subtotal': l.subtotal,

                # ✅ الصح
                'start_date': l.start_date,
                'end_date': l.end_date,
            }) for l in sorted_lines
        ]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.dashboard.viewer',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def sort_by_revenue(self):
        self.ensure_one()

        sorted_lines = self.line_ids.sorted(
            key=lambda l: l.subtotal,
            reverse=True
        )

        self.line_ids = [(5, 0, 0)] + [
            (0, 0, {
                'order_id': l.order_id.id,
                'unit_price': l.unit_price,
                'subtotal': l.subtotal,

                # ✅ الصح
                'start_date': l.start_date,
                'end_date': l.end_date,
            }) for l in sorted_lines
        ]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.dashboard.viewer',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        product_id = self.env.context.get('default_product_id')

        if product_id:
            states = self.env.context.get('states', [])

            domain = [
                ('product_id.product_tmpl_id', '=', product_id)
            ]

            if states:
                domain.append(('order_id.subscription_state', 'in', states))

            lines = self.env['sale.order.line'].search(domain)

            data = []
            total_unit = 0
            total_rev = 0
            total_amt = 0

            for line in lines:
                start_date = False
                end_date = False

                if line.name:
                    match = re.search(r'(\d{2}/\d{2}/\d{4}).*to (\d{2}/\d{2}/\d{4})', line.name)
                    if match:
                        start_date = datetime.strptime(match.group(1), '%m/%d/%Y').date()
                        end_date = datetime.strptime(match.group(2), '%m/%d/%Y').date()

                # 🔥 أهم جزء (كان ناقص)
                total_unit += line.price_unit
                total_rev += line.price_subtotal
                total_amt += line.price_total if hasattr(line, 'price_total') else line.price_subtotal

                data.append((0, 0, {
                    'order_id': line.order_id.id,
                    'unit_price': line.price_unit,
                    'subtotal': line.price_subtotal,
                    'start_date': start_date,
                    'end_date': end_date,
                }))
            res.update({
                'product_id': product_id,
                'line_ids': data,
                'total_unit_price': total_unit,
                'total_revenue': total_rev,
                'total_amount': total_amt,
                'line_count': len(lines),
            })

        return res


# =========================
# 🔥 PRODUCT LIST LINE (FIXED)
# =========================
class ProductListLine(models.Model):
    _name = 'product.list.line'

    dashboard_id = fields.Many2one('product.list.dashboard', ondelete='cascade')
    product_id = fields.Many2one('product.template')
    total_revenue = fields.Float(string="Total Revenue")
    name = fields.Char()
    list_price = fields.Float()
    standard_price = fields.Float()
    sequence = fields.Integer(default=0)

    def action_open_product_dashboard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Details',
            'res_model': 'product.dashboard.viewer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.product_id.id,
                'states': self.env.context.get('states')
            }
        }


# =========================
# 🔥 PRODUCT LIST DASHBOARD (FIXED)
# =========================
class ProductListDashboard(models.Model):
    _name = 'product.list.dashboard'

    def action_print_dashboard(self):
        return self.env.ref('custom_mexly_subscription.report_product_dashboard').report_action(self)

    total_revenue = fields.Float(string="Total Revenue")
    line_ids = fields.One2many(
        'product.list.line',
        'dashboard_id'
    )
    unit_type = fields.Selection([
        ('apartment', 'Apartment'),
        ('building', 'Building'),
        ('room', 'Room'),
        ('bed', 'Bed'),
        ('service', 'Service'),
    ])
    total_sales = fields.Float()
    total_cost = fields.Float()

    # 🔥 create data بدل default_get
    @api.model
    def create_dashboard(self, unit_type, states=None):
        record = self.create({
            'unit_type': unit_type
        })

        # 🔥 خزّن states في context
        record = record.with_context(states=states)

        SaleLine = self.env['sale.order.line']
        Product = self.env['product.template']

        # 🔥 تنظيف states
        states = states or []
        states = [s for s in states if s]
        print("FINAL STATES =", states)
        # 🔥 لو فيه states فعلاً
        if states:
            domain = [
                ('product_id.product_tmpl_id.unit_type', '=', unit_type),
                ('order_id.subscription_state', 'in', states)
            ]
            print("DOMAIN =", domain)
            lines = SaleLine.search(domain)
            print("LINES FOUND =", len(lines))

            # 🔥 لو مفيش lines → مفيش products
            if not lines:
                products = Product.browse([])
            else:
                products = Product.browse(
                    list(set(lines.mapped('product_id.product_tmpl_id').ids))
                )

        else:
            products = Product.search([
                ('unit_type', '=', unit_type)
            ])

        total_sales = 0
        total_cost = 0
        total_revenue = 0
        SaleLine = self.env['sale.order.line']

        for p in products:

            domain = [('product_id.product_tmpl_id', '=', p.id)]

            if states:
                domain.append(('order_id.subscription_state', 'in', states))

            lines = SaleLine.search(domain)

            revenue = sum(lines.mapped('price_subtotal'))

            self.env['product.list.line'].create({
                'dashboard_id': record.id,
                'product_id': p.id,
                'name': p.name,
                'list_price': p.list_price,
                'standard_price': p.standard_price,
                'total_revenue': revenue,  # 🔥 NEW
            })

            total_sales += p.list_price
            total_cost += p.standard_price
            total_revenue += revenue

        record.total_sales = total_sales
        record.total_cost = total_cost
        record.total_revenue = total_revenue  # 🔥 NEW
        return record

    # 🔥 SORT SALES
    def sort_by_sales(self):
        self.ensure_one()

        sorted_lines = self.line_ids.sorted(
            key=lambda l: l.list_price,
            reverse=True
        )

        for i, line in enumerate(sorted_lines):
            line.sequence = i

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.list.dashboard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',  # 🔥 دي أهم حاجة (يحافظ على popup)
        }

    # 🔥 SORT COST
    def sort_by_cost(self):
        self.ensure_one()

        sorted_lines = self.line_ids.sorted(
            key=lambda l: l.standard_price,
            reverse=True
        )

        for i, line in enumerate(sorted_lines):
            line.sequence = i

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.list.dashboard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


# =========================
# ACTION BUTTON (زي ما هو)
# =========================
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_open_product_dashboard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Details',
            'res_model': 'product.dashboard.viewer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id
            }
        }


class DashboardGraph(models.TransientModel):
    _name = 'dashboard.graph'

    name = fields.Char()
    value = fields.Float()


class SubscriptionStateHelper(models.Model):
    _name = 'subscription.state.helper'
    _description = 'Subscription State Helper'

    name = fields.Char()
    code = fields.Char()
