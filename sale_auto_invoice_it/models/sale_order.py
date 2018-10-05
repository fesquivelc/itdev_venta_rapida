from odoo import models, api, fields, _


class SaleOrderInvoice(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def auto_invoice(self, picking_ids=None):
        for sale in self:
            active_id = sale.id

            warehouse_id = sale.warehouse_id

            context = {'active_id': active_id, 'active_ids': [active_id]}
            apm = self.env['sale.advance.payment.inv'].with_context(context).create({'advance_payment_method': 'all'})
            apm.create_invoices()

            invoice = self.env['account.invoice'].search([('origin', '=', sale.name)], limit=1)
            invoice.write({
                'reference': sale.invoice_number,
                'it_type_document': sale.it_type_document.id,
                'serie_id': sale.it_invoice_serie.id
            })

            for line in invoice.invoice_line_ids:
                line.write({'location_id': sale.warehouse_id.lot_stock_id.id})

            if warehouse_id.account_id:
                invoice.write({
                    'account_id': warehouse_id.account_id.id,
                })

            if picking_ids:
                for picking_id in picking_ids:
                    picking_id.write({
                        'invoice_id': invoice.id
                    })

            # invoice.action_invoice_open()
            # reference = invoice.reference
            # invoice = self.env['account.invoice'].browse(invoice.id)
            # sale.write({
            #     'invoice_number': reference,
            # })
