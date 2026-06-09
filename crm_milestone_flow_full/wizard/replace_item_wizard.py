from odoo import api, fields, models
from odoo.exceptions import UserError


class ReplaceMilestoneItemWizard(models.TransientModel):
    _name = "wizard.replace.milestone.item"
    _description = "Replace Milestone Item"

    line_id = fields.Many2one("crm.milestone.line", required=True, readonly=True)
    milestone_id = fields.Many2one(
        "product.template",
        compute="_compute_milestone_id",
        store=False,
    )
    old_product_id = fields.Many2one(
        "product.product",
        string="Old Product",
        related="line_id.product_id",
        readonly=True,
    )
    product_type = fields.Selection(
        [
            ("consu", "Goods"),
            ("service", "Service"),
        ],
        compute="_compute_product_type",
        store=False,
    )
    new_product_id = fields.Many2one("product.product", string="New Product", required=True)
    qty = fields.Float(string="Quantity", required=True, default=1.0)
    pricing_method = fields.Selection(
        [
            ("margin", "Margin"),
            ("pricelist", "Pricelist"),
        ],
        string="Pricing",
        required=True,
        default="margin",
    )
    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist")
    manual_product_cost = fields.Float(string="Cost")
    margin = fields.Float(string="Margin (%)")
    pricelist_sale_price = fields.Float(
        string="Pricelist Sale Price",
        compute="_compute_prices",
        store=False,
    )
    unit_price = fields.Float(
        string="Unit Price",
    )

    @api.depends("line_id.type")
    def _compute_product_type(self):
        for wizard in self:
            wizard.product_type = "service" if wizard.line_id.type == "service" else "consu"

    @api.depends("line_id.goods_group_id.milestone_id", "line_id.service_group_id.milestone_id")
    def _compute_milestone_id(self):
        for wizard in self:
            group = wizard.line_id.goods_group_id or wizard.line_id.service_group_id
            wizard.milestone_id = group.milestone_id

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        line = self.env["crm.milestone.line"].browse(vals.get("line_id"))
        if line:
            vals.update({
                "qty": line.qty or 1.0,
                "pricing_method": line.pricing_method or "margin",
                "pricelist_id": line.pricelist_id.id,
                "manual_product_cost": line.manual_product_cost,
                "margin": line.margin,
                "unit_price": line.unit_price,
            })
        return vals

    def _get_partner(self):
        self.ensure_one()
        group = self.line_id.goods_group_id or self.line_id.service_group_id
        if not group:
            return False
        return group.sale_order_id.partner_id or group.lead_id.partner_id

    def _get_product_cost(self, product):
        return self.env["crm.milestone.line"]._get_product_cost(product)

    def _get_pricelist_price(self):
        self.ensure_one()
        if not self.new_product_id or not self.pricelist_id:
            return self.new_product_id.list_price if self.new_product_id else 0.0

        return self.pricelist_id._get_product_price(
            product=self.new_product_id,
            quantity=self.qty or 1.0,
            uom=self.new_product_id.uom_id,
            partner=self._get_partner(),
        )

    def _get_calculated_unit_price(self):
        self.ensure_one()
        if self.pricing_method == "pricelist":
            return (self._get_pricelist_price() or 0.0) * (self.qty or 0.0)

        return (
            (self.manual_product_cost or 0.0)
            * (self.qty or 0.0)
            * (1 + ((self.margin or 0.0) / 100))
        )

    @api.depends("new_product_id", "qty", "pricing_method", "pricelist_id")
    def _compute_prices(self):
        for wizard in self:
            if wizard.pricing_method == "pricelist":
                price = wizard._get_pricelist_price()
                wizard.pricelist_sale_price = price
            else:
                wizard.pricelist_sale_price = 0.0

    @api.onchange("new_product_id")
    def _onchange_new_product_id(self):
        for wizard in self:
            if wizard.new_product_id:
                wizard.manual_product_cost = wizard._get_product_cost(wizard.new_product_id)
            wizard.unit_price = wizard._get_calculated_unit_price()

    @api.onchange("qty", "pricing_method", "pricelist_id", "manual_product_cost", "margin")
    def _onchange_price_inputs(self):
        for wizard in self:
            wizard._compute_prices()
            wizard.unit_price = wizard._get_calculated_unit_price()

    @api.onchange("pricing_method")
    def _onchange_pricing_method(self):
        for wizard in self:
            if wizard.pricing_method == "pricelist" and not wizard.pricelist_id:
                partner = wizard._get_partner()
                wizard.pricelist_id = (
                    partner.property_product_pricelist
                    if partner and partner.property_product_pricelist
                    else self.env["product.pricelist"].search([], limit=1)
                )
            wizard._compute_prices()
            wizard.unit_price = wizard._get_calculated_unit_price()

    def _get_pricing_vals_matching_unit_price(self, new_product, qty):
        self.ensure_one()
        unit_price = self.unit_price or 0.0
        expected_unit_price = self._get_calculated_unit_price()
        pricing_method = self.pricing_method
        pricelist_id = self.pricelist_id.id
        manual_product_cost = self.manual_product_cost
        margin = self.margin

        if abs(unit_price - expected_unit_price) > 0.0001:
            pricing_method = "margin"
            pricelist_id = False
            manual_product_cost = manual_product_cost or self._get_product_cost(new_product)
            base_amount = (manual_product_cost or 0.0) * (qty or 0.0)
            if base_amount:
                margin = ((unit_price / base_amount) - 1) * 100
            else:
                manual_product_cost = unit_price / (qty or 1.0)
                margin = 0.0

        return {
            "pricing_method": pricing_method,
            "pricelist_id": pricelist_id,
            "manual_product_cost": manual_product_cost,
            "margin": margin,
        }

    def _find_sale_order_line(self):
        self.ensure_one()
        line = self.line_id
        if line.sale_order_line_id:
            return line.sale_order_line_id

        group = line.goods_group_id or line.service_group_id
        sale_order = group.sale_order_id
        if not sale_order:
            return self.env["sale.order.line"]

        candidates = sale_order.order_line.filtered(
            lambda sol: not sol.display_type
            and sol.product_id == line.product_id
            and abs((sol.product_uom_qty or 0.0) - (line.qty or 0.0)) < 0.0001
        )
        return candidates[:1]

    def _find_source_line(self):
        self.ensure_one()
        line = self.line_id
        if line.source_line_id:
            return line.source_line_id

        group = line.goods_group_id or line.service_group_id
        lead = group.sale_order_id.opportunity_id if group.sale_order_id else False
        if not lead:
            return self.env["crm.milestone.line"]

        crm_groups = lead.milestone_group_ids.filtered(lambda crm_group: crm_group.milestone_id == group.milestone_id)
        crm_lines = crm_groups.mapped("goods_line_ids" if line.type == "goods" else "service_line_ids")
        candidates = crm_lines.filtered(
            lambda crm_line: crm_line.product_id == line.product_id
            and abs((crm_line.qty or 0.0) - (line.qty or 0.0)) < 0.0001
        )
        return candidates[:1]

    def action_confirm_replace(self):
        self.ensure_one()
        line = self.line_id
        group = line.goods_group_id or line.service_group_id
        sale_order = group.sale_order_id
        if not sale_order:
            raise UserError("Replacement is available only from a Sales Order milestone group.")

        old_product = line.product_id
        new_product = self.new_product_id
        qty = self.qty or 1.0
        sale_order_line = self._find_sale_order_line()
        source_line = self._find_source_line()

        pricing_vals = self._get_pricing_vals_matching_unit_price(new_product, qty)
        vals = {
            "product_id": new_product.id,
            "qty": qty,
            "manual_product_sale_price": new_product.list_price,
            "replace_item": False,
            "line_update_state": "replaced",
        }
        vals.update(pricing_vals)
        line.write(vals)
        if source_line:
            source_line.write(vals)

        price_unit = (self.unit_price or 0.0) / qty
        if sale_order_line:
            taxes = new_product.taxes_id.filtered(lambda tax: tax.company_id == sale_order.company_id)
            if sale_order.fiscal_position_id:
                taxes = sale_order.fiscal_position_id.map_tax(taxes)
            sale_order_line.write({
                "product_id": new_product.id,
                "product_uom_qty": qty,
                "product_uom": new_product.uom_id.id,
                "price_unit": price_unit,
                "name": new_product.display_name,
                "tax_id": [(6, 0, taxes.ids)],
            })
            line.sale_order_line_id = sale_order_line.id

        group._update_sale_order_subsection_names()

        body = (
            f"Item replaced on Sales Order {sale_order.name}: "
            f"{old_product.display_name} -> {new_product.display_name} "
            f"(Qty: {qty})."
        )
        sale_order.message_post(body=body)
        if sale_order.opportunity_id:
            sale_order.opportunity_id.message_post(body=body)

        return {"type": "ir.actions.client", "tag": "reload"}
