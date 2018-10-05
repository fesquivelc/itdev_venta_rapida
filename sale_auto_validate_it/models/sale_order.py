# coding=utf-8
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class SaleOrderInvoice(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def auto_validate(self):
        self.action_confirm()

        picking_ids = self.env['stock.picking'].search([('origin', '=', self.name)])
        if picking_ids.exists():
            parameters = self.env['sale.parameters.it'].search([], limit=1)
            for picking_id in picking_ids:
                if parameters.force_assign:
                    picking_id.force_assign()
                for operation in picking_id.pack_operation_product_ids:
                    operation.write({'qty_done': operation.product_qty})
            # picking_id.do_new_transfer()
        else:
            raise ValidationError(_(u'No hay albarán de salida para la venta'))
        self.auto_invoice(picking_ids)

    @api.multi
    def picking_validate(self):
        for order in self:
            picking_ids = self.env['stock.picking'].search([('origin', '=', order.name)])
            if picking_ids.exists():
                for picking_id in picking_ids:
                    picking_id.do_new_transfer()
