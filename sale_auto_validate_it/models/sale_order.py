# coding=utf-8
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class SaleOrderInvoice(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def auto_validate(self):
        self.action_confirm()

        picking_id = self.env['stock.picking'].search([('origin', '=', self.name)], limit=1)
        if picking_id.exists():
            for operation in picking_id.pack_operation_product_ids:
                operation.write({'qty_done': operation.product_qty})
            picking_id.do_new_transfer()
        else:
            raise ValidationError(_(u'No hay albarán de salida para la venta'))
        self.auto_invoice()
