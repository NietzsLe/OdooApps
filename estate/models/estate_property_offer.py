from odoo import api, fields, models, exceptions
from datetime import datetime

fmt = "%Y-%m-%d"


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Estate Property Offer"

    price = fields.Float()
    status = fields.Selection(
        selection=[("accepted", "Accepted"), ("refused", "Refused")], copy=False
    )
    partner_id = fields.Many2one("res.partner", required=True)
    property_id = fields.Many2one("estate.property", required=True)
    validity = fields.Integer()
    deadline = fields.Date(compute="_compute_deadline", inverse="_inverse_deadline")

    _sql_constraints = [
        ("check_price", "CHECK(price > 0)", "This field expect value > 0.")
    ]

    @api.depends("validity")
    def _compute_deadline(self):
        for record in self:
            if record.create_date:
                record.deadline = fields.Date.add(
                    record.create_date, days=record.validity
                )
            else:
                record.deadline = fields.Date.add(
                    fields.Date.today(), days=record.validity
                )

    def _inverse_deadline(self):
        for record in self:
            d1 = datetime.strptime(fields.Date.to_string(record.create_date), fmt)
            d2 = datetime.strptime(fields.Date.to_string(record.deadline), fmt)
            record.validity = (d2 - d1).days

    def accept_handle(self):
        for record in self:
            if not record.status:
                for record1 in record.property_id.offer_ids:
                    if record1.status == "accepted":
                        record1.status = ""
                record.property_id.selling_price = record.price
                record.property_id.buyer_id = record.partner_id
                record.status = "accepted"
            else:
                raise exceptions.UserError("Can't change status again!")
        return True

    def refuse_handle(self):
        for record in self:
            if not record.status:
                record.status = "refused"
            else:
                raise exceptions.UserError("Can't change status again!")
        return True
