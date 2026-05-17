# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import UserError

from odoo.exceptions import ValidationError

ARKA_COMPANY_REGISTRY = "311369490700003"


class CrmMilestoneGroup(models.Model):
    _name = "crm.milestone.group"
    _description = "Milestone Group"

    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")

    planned_date_from = fields.Date(
        string="Planned Date From",
    )

    planned_date_to = fields.Date(
        string="Planned Date To",
    )
    total_sale_milestone = fields.Float(
        string="Total Sale",
        compute="_compute_totals",
        store=True
    )

    quantity = fields.Float(string="Quantity Milestone", default=1, store=True)
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        ondelete="cascade"
    )
    total_cost = fields.Float(
        string="Total Cost (G+S)",
        compute="_compute_total_cost",
        store=True
    )

    @api.depends(
        "total_goods_cost",
        "total_service_cost"
    )
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = (rec.total_goods_cost or 0.0) + (rec.total_service_cost or 0.0)

    def action_open_po_wizard(self):
        self.ensure_one()
        return {
            'name': "Create Purchase Order",
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.create.po',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_group_idx': self.id,
            }
        }

    def action_open_job_order_wizard(self):
        self.ensure_one()
        return {
            'name': "Create Job Order",
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.create.job.order',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_group_idx': self.id,
            }
        }

    stage = fields.Selection([
        ('project', 'إدارة المشروع'),
        ('technical', 'المكتب الفني'),

    ], string="Stage", default='technical')

    def action_to_technical(self):
        for rec in self:
            rec.stage = 'technical'

    def action_to_project(self):
        for rec in self:
            rec.stage = 'project'

    lead_id = fields.Many2one("crm.lead", string="Opportunity", ondelete="cascade")

    milestone_id = fields.Many2one(
        "product.template",
        domain=[('is_milestone_flag', '=', True)],
        string="Milestone"
    )

    def action_open_goods_popup(self):
        self.ensure_one()
        return {
            'name': 'Select Goods',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.goods.selector',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.lead_id.id,
                'default_milestone_id': self.milestone_id.id,
                'force_type': 'goods',
                'default_group_idx': self.id,
            }
        }

    def action_open_services_popup(self):
        self.ensure_one()
        return {
            'name': 'Select Services',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.services.selector',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.lead_id.id,
                'default_milestone_id': self.milestone_id.id,
                'force_type': 'service',
                'default_group_idx': self.id,
            }
        }

    def _get_pipeline_group(self):
        self.ensure_one()
        sale_order = self.sale_order_id
        lead = sale_order.opportunity_id if sale_order else self.lead_id
        if not lead:
            return False

        pipeline_group = lead.milestone_group_ids.filtered(
            lambda group: group.milestone_id == self.milestone_id
        )[:1]
        if pipeline_group:
            return pipeline_group

        return self.create({
            "lead_id": lead.id,
            "milestone_id": self.milestone_id.id,
            "quantity": self.quantity,
            "planned_date_from": self.planned_date_from,
            "planned_date_to": self.planned_date_to,
            "stage": self.stage,
        })

    def _get_sale_order_subsection(self, line_type):
        self.ensure_one()
        sale_order = self.sale_order_id
        if not sale_order:
            return self.env["sale.order.line"]

        lines = sale_order.order_line.sorted(lambda line: (line.sequence, line.id))
        milestone_section = lines.filtered(
            lambda line: line.display_type == "line_section" and line.name == self.milestone_id.name
        )[:1]
        if not milestone_section:
            milestone_section = self.env["sale.order.line"].create({
                "order_id": sale_order.id,
                "name": self.milestone_id.name,
                "display_type": "line_section",
            })
            lines = sale_order.order_line.sorted(lambda line: (line.sequence, line.id))

        label = "Goods" if line_type == "goods" else "Services"
        ordered_lines = list(lines)
        ordered_line_ids = [order_line.id for order_line in ordered_lines]
        start_index = ordered_line_ids.index(milestone_section.id)
        group_lines = []
        for order_line in ordered_lines[start_index + 1:]:
            is_section = order_line.display_type == "line_section"
            is_subsection = (order_line.name or "").startswith(("Goods", "Services"))
            if is_section and not is_subsection:
                break
            group_lines.append(order_line)

        subsection = self.env["sale.order.line"]
        for order_line in group_lines:
            if order_line.display_type == "line_section" and (order_line.name or "").startswith(label):
                subsection = order_line
                break

        if not subsection:
            total = self.total_goods_unit_price if line_type == "goods" else self.total_service_unit_price
            subsection = self.env["sale.order.line"].create({
                "order_id": sale_order.id,
                "name": f"{label} - Total Unit Price: {total or 0.0:.2f}",
                "display_type": "line_section",
                "sequence": milestone_section.sequence + 1,
            })
        return subsection

    def _find_sale_order_subsection(self, line_type):
        self.ensure_one()
        sale_order = self.sale_order_id
        if not sale_order:
            return self.env["sale.order.line"]

        lines = sale_order.order_line.sorted(lambda line: (line.sequence, line.id))
        milestone_section = lines.filtered(
            lambda line: line.display_type == "line_section" and line.name == self.milestone_id.name
        )[:1]
        if not milestone_section:
            return self.env["sale.order.line"]

        label = "Goods" if line_type == "goods" else "Services"
        ordered_lines = list(lines)
        ordered_line_ids = [order_line.id for order_line in ordered_lines]
        start_index = ordered_line_ids.index(milestone_section.id)
        for order_line in ordered_lines[start_index + 1:]:
            is_section = order_line.display_type == "line_section"
            is_subsection = (order_line.name or "").startswith(("Goods", "Services"))
            if is_section and not is_subsection:
                break
            if is_section and (order_line.name or "").startswith(label):
                return order_line
        return self.env["sale.order.line"]

    def _update_sale_order_subsection_names(self):
        for group in self.filtered("sale_order_id"):
            if group.goods_line_ids:
                goods_section = group._get_sale_order_subsection("goods")
                goods_total = sum(group.goods_line_ids.mapped("unit_price"))
                goods_section.name = f"Goods - Total Unit Price: {goods_total or 0.0:.2f}"
            else:
                goods_section = group._find_sale_order_subsection("goods")
                if goods_section:
                    goods_section.unlink()
            if group.service_line_ids:
                service_section = group._get_sale_order_subsection("service")
                service_total = sum(group.service_line_ids.mapped("unit_price"))
                service_section.name = f"Services - Total Unit Price: {service_total or 0.0:.2f}"
            else:
                service_section = group._find_sale_order_subsection("service")
                if service_section:
                    service_section.unlink()

    def _create_sale_order_line_for_milestone_line(self, milestone_line, line_type):
        self.ensure_one()
        sale_order = self.sale_order_id
        if not sale_order:
            return self.env["sale.order.line"]

        subsection = self._get_sale_order_subsection(line_type)
        lines = sale_order.order_line.sorted(lambda line: (line.sequence, line.id))
        after_subsection = lines.filtered(lambda line: line.sequence > subsection.sequence)
        next_section = after_subsection.filtered("display_type")[:1]
        section_lines = after_subsection.filtered(
            lambda line: not next_section or line.sequence < next_section.sequence
        )
        insert_sequence = max([subsection.sequence] + section_lines.mapped("sequence")) + 1
        if next_section and insert_sequence >= next_section.sequence:
            following_lines = lines.filtered(lambda line: line.sequence >= next_section.sequence)
            for line in following_lines:
                line.sequence += 10

        product = milestone_line.product_id
        qty = milestone_line.qty or 1.0
        taxes = product.taxes_id.filtered(lambda tax: tax.company_id == sale_order.company_id)
        if sale_order.fiscal_position_id:
            taxes = sale_order.fiscal_position_id.map_tax(taxes)

        return self.env["sale.order.line"].create({
            "order_id": sale_order.id,
            "sequence": insert_sequence,
            "product_id": product.id,
            "product_uom_qty": qty,
            "product_uom": product.uom_id.id,
            "price_unit": (milestone_line.unit_price or 0.0) / qty,
            "name": milestone_line.description or product.display_name,
            "tax_id": [(6, 0, taxes.ids)],
        })

    def add_products_from_selector(self, products, line_type):
        for group in self:
            for product in products:
                if group.sale_order_id:
                    pipeline_group = group._get_pipeline_group()
                    pipeline_vals = {
                        "product_id": product.id,
                        "qty": 1.0,
                        "type": line_type,
                        "line_update_state": "added_sale_order",
                    }
                    if line_type == "goods":
                        pipeline_vals.update({
                            "goods_group_id": pipeline_group.id,
                            "goods_lead_id": pipeline_group.lead_id.id,
                        })
                    else:
                        pipeline_vals.update({
                            "service_group_id": pipeline_group.id,
                            "service_lead_id": pipeline_group.lead_id.id,
                        })
                    source_line = self.env["crm.milestone.line"].create(pipeline_vals)

                    order_vals = dict(pipeline_vals)
                    order_vals.pop("goods_lead_id", None)
                    order_vals.pop("service_lead_id", None)
                    order_vals["source_line_id"] = source_line.id
                    if line_type == "goods":
                        order_vals["goods_group_id"] = group.id
                    else:
                        order_vals["service_group_id"] = group.id
                    order_line = self.env["crm.milestone.line"].create(order_vals)
                    sale_order_line = group._create_sale_order_line_for_milestone_line(order_line, line_type)
                    order_line.sale_order_line_id = sale_order_line.id
                    group._update_sale_order_subsection_names()

                    body = (
                        f"New {line_type} item added from Sales Order {group.sale_order_id.name}: "
                        f"{product.display_name}."
                    )
                    group.sale_order_id.message_post(body=body)
                    if group.sale_order_id.opportunity_id:
                        group.sale_order_id.opportunity_id.message_post(body=body)
                else:
                    vals = {
                        "product_id": product.id,
                        "type": line_type,
                        "line_update_state": "from_pipeline",
                    }
                    if line_type == "goods":
                        vals.update({
                            "goods_group_id": group.id,
                            "goods_lead_id": group.lead_id.id,
                        })
                    else:
                        vals.update({
                            "service_group_id": group.id,
                            "service_lead_id": group.lead_id.id,
                        })
                    self.env["crm.milestone.line"].create(vals)

    # goods + services lines for this group ONLY
    goods_line_ids = fields.One2many(
        "crm.milestone.line",
        "goods_group_idx",
        string="Goods Lines"
    )

    service_line_ids = fields.One2many(
        "crm.milestone.line",
        "service_group_idx",
        string="Service Lines"
    )
    goods_line_ids = fields.One2many("crm.milestone.line", "goods_group_id")
    service_line_ids = fields.One2many("crm.milestone.line", "service_group_id")

    # totals (store=False عشان تتحدث فوراً وما تختفيش)
    total_goods_cost = fields.Float(compute="_compute_totals", store=True)
    total_goods_unit_price = fields.Float(compute="_compute_totals", store=True)
    total_goods_sale = fields.Float(compute="_compute_totals", store=False)

    total_service_cost = fields.Float(compute="_compute_totals", store=True)
    total_service_unit_price = fields.Float(compute="_compute_totals", store=True)
    total_service_sale = fields.Float(compute="_compute_totals", store=False)

    @api.depends(
        "goods_line_ids.unit_price",
        "goods_line_ids.qty",
        "goods_line_ids.manual_product_cost",
        "goods_line_ids.manual_product_sale_price",
        "goods_line_ids.pricelist_sale_price",
        "goods_line_ids.pricing_method",
        "goods_line_ids.pricelist_id",
        "service_line_ids.unit_price",
        "service_line_ids.qty",
        "service_line_ids.manual_product_cost",
        "service_line_ids.manual_product_sale_price",
        "service_line_ids.pricelist_sale_price",
        "service_line_ids.pricing_method",
        "service_line_ids.pricelist_id",
        "quantity",
    )
    def _compute_totals(self):
        """Recompute totals dynamically. Always correct & never disappears."""
        for rec in self:
            # GOODS
            rec.total_goods_cost = sum(line.manual_product_cost * line.qty for line in rec.goods_line_ids)
            rec.total_goods_unit_price = sum(line.unit_price for line in rec.goods_line_ids)
            rec.total_goods_sale = (
                rec.total_goods_unit_price / rec.quantity if rec.quantity else 0.0
            )

            # rec.total_goods_sale = sum(line.manual_product_sale_price * line.qty for line in rec.goods_line_ids)

            # SERVICES
            rec.total_service_cost = sum(line.manual_product_cost * line.qty for line in rec.service_line_ids)
            rec.total_service_unit_price = sum(line.unit_price for line in rec.service_line_ids)
            rec.total_service_sale = (
                rec.total_service_unit_price / rec.quantity if rec.quantity else 0.0
            )
            # rec.total_service_sale = sum(line.manual_product_sale_price * line.qty for line in rec.service_line_ids)
            rec.total_sale_milestone = (
                    rec.total_goods_sale + rec.total_service_sale
            )

class CrmMilestoneLine(models.Model):
    _name = "crm.milestone.line"
    _description = "Milestone Line"
    _order = "id desc"

    po_line_ids = fields.One2many(
        "purchase.order.line",
        "milestone_line_id",
        string="Related PO Lines"
    )

    delivered_quantity = fields.Float(
        string="Delivered Qty",
        compute="_compute_delivered_quantity",
        store=False
    )

    @api.depends("po_line_ids.qty_received")
    def _compute_delivered_quantity(self):
        for rec in self:
            rec.delivered_quantity = sum(rec.po_line_ids.mapped("qty_received"))

    selected_for_po = fields.Boolean(
        string="Select for PO",
        help="Include this line when creating Purchase Order."
    )

    replace_item = fields.Boolean(
        string="Replace",
        help="Select this line to replace it from the Sales Order milestone group."
    )

    source_line_id = fields.Many2one(
        "crm.milestone.line",
        string="CRM Source Line",
        ondelete="set null",
        copy=False,
    )

    sale_order_line_id = fields.Many2one(
        "sale.order.line",
        string="Sale Order Line",
        ondelete="set null",
        copy=False,
    )

    line_update_state = fields.Selection(
        [
            ("from_pipeline", "📌 Added from Pipeline"),
            ("replaced", "🔁 Modified by Replace"),
            ("added_sale_order", "✨ New from Sales Order"),
        ],
        string="Line Status",
        default="from_pipeline",
        copy=True,
    )

    def action_open_replace_item_wizard(self):
        self.ensure_one()
        if not self._get_group().sale_order_id:
            raise UserError("Replacement is available only from a Sales Order milestone group.")
        return {
            "name": "Replace Item",
            "type": "ir.actions.act_window",
            "res_model": "wizard.replace.milestone.item",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_line_id": self.id,
            },
        }

    def _find_linked_sale_order_line(self):
        self.ensure_one()
        if self.sale_order_line_id:
            return self.sale_order_line_id

        group = self._get_group()
        sale_order = group.sale_order_id
        if not sale_order:
            return self.env["sale.order.line"]

        candidates = sale_order.order_line.filtered(
            lambda line: not line.display_type
            and line.product_id == self.product_id
            and abs((line.product_uom_qty or 0.0) - (self.qty or 0.0)) < 0.0001
        )
        return candidates[:1]

    def _find_linked_source_line(self):
        self.ensure_one()
        if self.source_line_id:
            return self.source_line_id

        group = self._get_group()
        sale_order = group.sale_order_id
        lead = sale_order.opportunity_id if sale_order else False
        if not lead:
            return self.env["crm.milestone.line"]

        pipeline_groups = lead.milestone_group_ids.filtered(
            lambda pipeline_group: pipeline_group.milestone_id == group.milestone_id
        )
        pipeline_lines = pipeline_groups.mapped("goods_line_ids" if self.type == "goods" else "service_line_ids")
        candidates = pipeline_lines.filtered(
            lambda line: line.product_id == self.product_id
            and abs((line.qty or 0.0) - (self.qty or 0.0)) < 0.0001
        )
        return candidates[:1]

    def unlink(self):
        sync_payload = []
        for line in self:
            group = line._get_group()
            sale_order = group.sale_order_id if group else False
            if not sale_order:
                continue

            sync_payload.append({
                "group": group,
                "sale_order": sale_order,
                "lead": sale_order.opportunity_id,
                "product_name": line.product_id.display_name,
                "line_type": line.type or "item",
                "sale_order_line": line._find_linked_sale_order_line(),
                "source_line": line._find_linked_source_line(),
            })

        for payload in sync_payload:
            source_line = payload["source_line"]
            if source_line and source_line.exists() and source_line not in self:
                source_line.unlink()

            sale_order_line = payload["sale_order_line"]
            if sale_order_line and sale_order_line.exists():
                sale_order_line.unlink()

        result = super().unlink()

        for payload in sync_payload:
            group = payload["group"]
            if group.exists():
                group._update_sale_order_subsection_names()

            body = (
                f"{payload['line_type'].title()} item deleted from Sales Order "
                f"{payload['sale_order'].name}: {payload['product_name']}."
            )
            payload["sale_order"].message_post(body=body)
            if payload["lead"]:
                payload["lead"].message_post(body=body)

        return result

    # NEW: Manual fields (بديل للـ related)
    manual_product_cost = fields.Float(
        string="Cost",
        compute="_compute_manual_product_cost",
        inverse="_inverse_manual_product_cost",
        store=True,
        readonly=False,
    )

    manual_product_sale_price = fields.Float(
        string="Sale Price"
    )

    pricing_method = fields.Selection(
        [
            ('margin', 'Margin'),
            ('pricelist', 'Pricelist'),
        ],
        string="Pricing",
        default='margin',
        required=True,
    )

    pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Pricelist",
    )

    pricelist_sale_price = fields.Float(
        string="Pricelist Sale Price",
        compute="_compute_pricelist_sale_price",
        store=False,
    )

    current_stage = fields.Selection(
        [
            ('technical', 'المكتب الفني'),
            ('project', 'إدارة المشروع'),
        ],
        string="Stage",
        compute="_compute_current_stage",
        store=False,
    )

    @api.depends("goods_group_id.stage", "service_group_id.stage")
    def _compute_current_stage(self):
        for rec in self:
            rec.current_stage = rec.goods_group_id.stage or rec.service_group_id.stage

    goods_group_id = fields.Many2one("crm.milestone.group", string="Goods Group")
    service_group_id = fields.Many2one("crm.milestone.group", string="Service Group")

    total_price = fields.Float(
        string="Total",
        compute="_compute_unit_price",
        store=False
    )

    margin = fields.Float(string="Margin (%)")
    unit_price = fields.Float(
        string="Unit Price",
        compute="_compute_unit_price",
        store=False
    )

    @api.depends("product_id")
    def _compute_manual_product_cost(self):
        for rec in self:
            if rec.product_id and not rec.manual_product_cost:
                rec.manual_product_cost = rec._get_product_cost(rec.product_id)
            else:
                rec.manual_product_cost = rec.manual_product_cost or 0.0

    def _inverse_manual_product_cost(self):
        pass

    def _get_group(self):
        self.ensure_one()
        return self.goods_group_id or self.service_group_id

    def _get_pricing_partner(self):
        self.ensure_one()
        group = self._get_group()
        if not group:
            return False
        return group.lead_id.partner_id or group.sale_order_id.partner_id

    def _get_default_pricelist(self):
        self.ensure_one()
        partner = self._get_pricing_partner()
        if partner and partner.property_product_pricelist:
            return partner.property_product_pricelist
        return self.env["product.pricelist"].search([], limit=1)

    def _get_product_cost(self, product):
        if not product:
            return 0.0

        if product.standard_price:
            return product.standard_price

        purchase_lines = self.env["purchase.order.line"].search([
            ("product_id", "=", product.id),
            ("order_id.state", "in", ["purchase", "done"]),
        ], order="id desc", limit=50)
        purchase_line = purchase_lines.sorted(
            lambda line: (line.order_id.date_order or fields.Datetime.to_datetime("1970-01-01"), line.id),
            reverse=True,
        )[:1]

        if not purchase_line:
            return product.standard_price or 0.0

        price = (
            purchase_line.price_unit_discounted
            if "price_unit_discounted" in purchase_line._fields
            else purchase_line.price_unit
        )
        price = price or 0.0

        company = purchase_line.company_id or self.env.company
        order = purchase_line.order_id
        if order.currency_id and order.currency_id != company.currency_id:
            price = order.currency_id._convert(
                price,
                company.currency_id,
                company,
                order.date_order or fields.Date.today(),
            )

        if purchase_line.product_uom and purchase_line.product_uom != product.uom_id:
            price = purchase_line.product_uom._compute_price(price, product.uom_id)

        return price

    def _get_pricelist_price(self):
        self.ensure_one()
        if not self.product_id or not self.pricelist_id:
            return self.manual_product_sale_price or self.product_sale_price or 0.0

        partner = self._get_pricing_partner()
        quantity = self.qty or 1.0
        pricelist = self.pricelist_id

        return pricelist._get_product_price(
            product=self.product_id,
            quantity=quantity,
            uom=self.product_uom,
            partner=partner,
        )

    @api.depends(
        "product_id",
        "qty",
        "manual_product_sale_price",
        "product_sale_price",
        "pricing_method",
        "pricelist_id",
        "goods_group_id.lead_id.partner_id",
        "goods_group_id.sale_order_id.partner_id",
        "service_group_id.lead_id.partner_id",
        "service_group_id.sale_order_id.partner_id",
    )
    def _compute_pricelist_sale_price(self):
        for rec in self:
            rec.pricelist_sale_price = rec._get_pricelist_price()

    @api.depends(
        "manual_product_cost",
        "manual_product_sale_price",
        "product_cost",
        "product_sale_price",
        "margin",
        "qty",
        "pricing_method",
        "pricelist_sale_price",
    )
    def _compute_unit_price(self):
        for rec in self:
            if rec.pricing_method == "pricelist":
                rec.unit_price = (rec.pricelist_sale_price or 0.0) * (rec.qty or 0.0)
                rec.total_price = rec.unit_price
                continue

            cost = rec.manual_product_cost or 0.0
            rec.unit_price = cost * (rec.qty or 0.0) * (1 + ((rec.margin or 0.0) / 100))
            rec.total_price = rec.unit_price

    @api.onchange("product_id")
    def _onchange_product_prices(self):
        for rec in self:
            if rec.product_id:
                rec.manual_product_cost = rec._get_product_cost(rec.product_id)
                rec.manual_product_sale_price = rec.product_id.list_price

    @api.onchange("manual_product_cost", "margin", "qty", "pricing_method", "pricelist_id")
    def _onchange_price_inputs(self):
        self._compute_unit_price()

    @api.onchange("pricing_method", "goods_group_id", "service_group_id")
    def _onchange_pricing_method(self):
        for rec in self:
            if rec.pricing_method == "pricelist" and not rec.pricelist_id:
                rec.pricelist_id = rec._get_default_pricelist()

    @api.model_create_multi
    def create(self, vals_list):
        Product = self.env["product.product"]
        for vals in vals_list:
            product_id = vals.get("product_id")
            if product_id:
                product = Product.browse(product_id)
                if not vals.get("manual_product_cost"):
                    vals["manual_product_cost"] = self._get_product_cost(product)
                if not vals.get("manual_product_sale_price"):
                    vals["manual_product_sale_price"] = product.list_price
            if vals.get("pricing_method") == "pricelist" and not vals.get("pricelist_id"):
                temp_line = self.new(vals)
                default_pricelist = temp_line._get_default_pricelist()
                if default_pricelist:
                    vals["pricelist_id"] = default_pricelist.id
        return super().create(vals_list)

    goods_lead_id = fields.Many2one("crm.lead", string="Goods Lead")
    service_lead_id = fields.Many2one("crm.lead", string="Service Lead")

    product_default_code = fields.Char(
        string="Internal Reference",
        related="product_id.default_code",
        store=False
    )

    product_barcode = fields.Char(
        string="Barcode",
        related="product_id.barcode",
        store=False
    )

    product_cost = fields.Float(
        string="Cost",
        related="product_id.standard_price",
        store=False
    )

    product_sale_price = fields.Float(
        string="Sale Price",
        related="product_id.list_price",
        store=False
    )

    product_uom = fields.Many2one(
        "uom.uom",
        string="UoM",
        related="product_id.uom_id",
        store=False
    )

    product_variants = fields.Many2many(
        "product.attribute.value",
        string="Variants",
        compute="_compute_product_variants",
        store=False
    )

    @api.depends("product_id")
    def _compute_product_variants(self):
        for rec in self:
            if rec.product_id:
                rec.product_variants = rec.product_id.product_template_attribute_value_ids.mapped(
                    "product_attribute_value_id")
            else:
                rec.product_variants = False

    lead_id = fields.Many2one("crm.lead", ondelete="cascade", string="Opportunity")
    product_id = fields.Many2one("product.product", string="Product", required=True)
    qty = fields.Float(string="Quantity", default=1.0)
    price = fields.Float(string="Unit Price", related="product_id.list_price", store=True)
    type = fields.Selection([('goods', 'Goods'), ('service', 'Service')], string="Type")
    description = fields.Char(string="Description")


class CrmLead(models.Model):
    _inherit = "crm.lead"


    total_cost_project = fields.Float(
        string="Total Cost Project",
        compute="_compute_totals_project",
        store=False
    )

    total_unit_price_project = fields.Float(
        string="Total Unit Price Project",
        compute="_compute_totals_project",
        store=False
    )

    show_unit_price_field = fields.Boolean(
        compute="_compute_show_unit_price_field",
        store=False
    )

    @api.depends("stage_id")
    def _compute_show_unit_price_field(self):
        for rec in self:
            rec.show_unit_price_field = rec.stage_id.name != "Technical Office"

    @api.depends("milestone_group_ids.total_cost",
                 "milestone_group_ids.total_goods_unit_price",
                 "milestone_group_ids.total_service_unit_price")
    def _compute_totals_project(self):
        for rec in self:
            rec.total_cost_project = sum(g.total_cost for g in rec.milestone_group_ids)
            rec.total_unit_price_project = sum(
                (g.total_goods_unit_price or 0.0) + (g.total_service_unit_price or 0.0)
                for g in rec.milestone_group_ids
            )

    milestone_group_ids = fields.One2many(
        "crm.milestone.group",
        "lead_id",
        string="Milestone Groups"
    )

    def action_add_milestone_group(self):
        self.ensure_one()
        self.env["crm.milestone.group"].create({"lead_id": self.id})

    milestone_id = fields.Many2one(
        "product.template",
        domain=[('is_milestone_flag', '=', True)],
        string="Milestone",
        help="Select the milestone for this opportunity (Arka only)."
    )
    milestone_line_ids = fields.One2many(
        "crm.milestone.line", "lead_id", string="Milestone Lines"
    )
    milestone_line_goods_ids = fields.One2many(
        "crm.milestone.line",
        "goods_lead_id",
        string="Goods Lines"
    )

    milestone_line_service_ids = fields.One2many(
        "crm.milestone.line",
        "service_lead_id",
        string="Service Lines"
    )

    is_proposition_stage = fields.Boolean(
        compute="_compute_is_proposition_stage",
        store=False
    )
    is_arka_company = fields.Boolean(
        compute="_compute_is_arka_company",
        store=False
    )

    def _compute_is_arka_company(self):
        for r in self:
            r.is_arka_company = (r.env.company.company_registry == ARKA_COMPANY_REGISTRY)

    def _compute_is_proposition_stage(self):
        for r in self:
            r.is_proposition_stage = (r.stage_id and r.stage_id.name == 'Technical Office')

    def action_open_goods_popup(self):
        self.ensure_one()
        if not self.milestone_id:
            raise UserError('Please select a Milestone first.')
        return {
            'name': 'Select Goods for Milestone',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.goods.selector',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_milestone_id': self.milestone_id.id,
                'force_type': 'goods',
            }
        }

    def action_open_services_popup(self):
        self.ensure_one()
        if not self.milestone_id:
            raise UserError('Please select a Milestone first.')
        return {
            'name': 'Select Services for Milestone',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.services.selector',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_milestone_id': self.milestone_id.id,
                'force_type': 'service',
            }
        }



# add
class WizardCreatePO(models.TransientModel):
    _name = "wizard.create.po"
    _description = "Create PO Wizard"

    group_idx = fields.Many2one("crm.milestone.group")

    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
    )

    # ➤ إضافة اختيار Service هنا
    po_type = fields.Selection(
        [
            ('inventory', "With Inventory Material"),
            ('non_inventory', "Non Inventory Material"),
            ('service', "Service"),
        ],
        string="Material Type",
        required=True
    )

    def action_confirm_create_po(self):
        self.ensure_one()
        group = self.group_idx

        # ============================================
        # 1) SELECT LINES BASED ON TYPE
        # ============================================
        if self.po_type == "service":
            # خــدمــات فقط
            lines = group.service_line_ids.filtered(lambda l: l.selected_for_po)
            if not lines:
                lines = group.service_line_ids

        else:
            # Goods فقط (inventory + non-inventory)
            lines = group.goods_line_ids.filtered(lambda l: l.selected_for_po)
            if not lines:
                lines = group.goods_line_ids

        if not lines:
            raise UserError("No products selected for purchase order.")

        # ============================================
        # 2) GET PROJECT + SALE ORDER
        # ============================================
        sale_order = group.sale_order_id
        project = sale_order.project_id if sale_order else False

        # ============================================
        # 3) DETERMINE LOCATION
        # ============================================
        StockLocation = self.env["stock.location"].search([
            ("company_id", "=", self.env.company.id),
            ("usage", "=", "internal"),
            ("name", "=", "Stock"),
        ], limit=1)

        if not StockLocation:
            raise UserError("Could not find WH/Stock location for this company.")

        # ➤ اختيار Service → بدون Location نهائياً
        if self.po_type == "service":
            location_dest = False

        # ➤ Inventory → WH/Stock
        elif self.po_type == "inventory":
            location_dest = StockLocation

        # ➤ Non-inventory → يعمل / يعيد استخدام موقع المشروع
        else:
            if not project:
                raise UserError("No project selected in this sale order.")

            if not project.location_id:
                raise UserError("Project has no location. اعمل confirm الأول")

            location_dest = project.location_id

        # ============================================
        # 4) CREATE PURCHASE ORDER
        # ============================================
        po_vals = {
            "partner_id": self.vendor_id.id,
            "project_id": project.id if project else False,
            "origin": f"Milestone: {group.milestone_id.name}",
            "milestone_po": True,
            "milestone_type": self.po_type,
        }

        # ➤ محدد location فقط لو مش Service
        if location_dest:
            po_vals["milestone_location_dest_id"] = location_dest.id

        po = self.env["purchase.order"].create(po_vals)

        # حفظ آخر location فقط لو مش Service
        if sale_order and location_dest:
            sale_order.last_po_location_id = location_dest

        # ============================================
        # 5) CREATE PO LINES
        # ============================================
        for line in lines:
            self.env["purchase.order.line"].create({
                "order_id": po.id,
                "product_id": line.product_id.id,
                "name": line.product_id.display_name,
                "product_qty": line.qty,
                "price_unit": line.manual_product_cost,
                "date_planned": fields.Date.today(),
                "product_uom": line.product_uom.id,
                "milestone_line_id": line.id,
            })

        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": po.id,
        }



class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    milestone_location_dest_id = fields.Many2one(
        "stock.location",
        string="Milestone Destination Location",
        invisible=True
    )

    def _prepare_picking(self):
        vals = super()._prepare_picking()

        if self.milestone_location_dest_id:
            vals["location_dest_id"] = self.milestone_location_dest_id.id

        return vals

    @api.constrains('group_idx')
    def _check_group_id_valid(self):
        for rec in self:
            if rec.group_idx and not self.env['crm.milestone.group'].search([('id', '=', rec.group_idx.id)], limit=1):
                raise ValidationError("Invalid Milestone Group! This group does not exist.")


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    milestone_line_id = fields.Many2one(
        "crm.milestone.line",
        string="Milestone Line",
        ondelete="set null"
    )

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()

        for picking in self:
            po = self.env["purchase.order"].search([
                ("name", "=", picking.origin)
            ], limit=1)

            if po and po.milestone_location_dest_id:
                new_loc = po.milestone_location_dest_id.id

                # 🔥 ده المهم الحقيقي
                for move_line in picking.move_line_ids:
                    move_line.location_dest_id = new_loc

        return res
