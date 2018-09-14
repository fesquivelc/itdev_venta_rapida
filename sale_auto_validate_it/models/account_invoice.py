# coding=utf-8
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        result = super(AccountInvoice, self).action_invoice_open()
        for inv in self:
            order = self.env['sale.order'].search([('name', '=', inv.origin)], limit=1)
            order.picking_validate()

            reference = inv.reference
            order.write({
                'invoice_number': reference,
            })
        return result
