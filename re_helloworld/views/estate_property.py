from odoo import api, fields, models, exceptions
from odoo.tools.float_utils import float_compare


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"

    name = fields.Char(required=True)
    description = fields.Char()
    postcode = fields.Char()
    date_availability = fields.Date(
        copy=False, default=fields.Date.add(fields.Date.today(), months=3)
    )
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        selection=[
            ("north", "North"),
            ("south", "South"),
            ("east", "East"),
            ("west", "West"),
        ]
    )
    state = fields.Selection(
        selection=[
            ("offer_received", "Offer Received"),
            ("offer_accept", "Offer Accept"),
            ("sold", "Sold"),
            ("canceled", "Canceled"),
            ("new", "New"),
        ],
        default="new",
        copy=False,
        groups="re_helloworld.estate_group_property_manager",
    )
    salesperson_id = fields.Many2one(
        "res.users", string="Salesperson", default=lambda self: self.env.user
    )
    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False)
    property_type_id = fields.Many2one("estate.property.type", string="Type")
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    total_area = fields.Integer(compute="_compute_total_area")
    best_price = fields.Float(compute="_compute_best_price")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "check_expected_price",
            "CHECK(expected_price > 0)",
            "This field expect value > 0.",
        ),
        (
            "check_selling_price",
            "CHECK(selling_price >= 0)",
            "This field expect value >= 0.",
        ),
    ]

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            record.best_price = max([0] + record.offer_ids.mapped("price"))

    @api.onchange("garden")
    def _onchange_garder(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = ""

    def sold_handle(self):
        for record in self:
            if record.state == "canceled":
                raise exceptions.UserError("Can't sold a canceled property")
            else:
                record.state = "sold"
        return True

    def cancel_handle(self):
        for record in self:
            if record.state == "sold":
                raise exceptions.UserError("Can't cancel a sold property")
            else:
                record.state = "canceled"
        return True

    @api.constrains("selling_price")
    def _check_selling_price_90per(self):
        for record in self:
            compare_result = float_compare(
                record.selling_price, record.expected_price * 0.9, 2
            )
            if compare_result == -1:

                raise exceptions.ValidationError(
                    "Selling price must be equal or higher than 90% Expect price."
                )
