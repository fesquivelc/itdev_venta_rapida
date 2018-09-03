from odoo import models, api, fields, _


class SaleOrderInvoice(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def auto_invoice(self):
        for sale in self:
            active_id = sale.id

            warehouse_id = self.warehouse_id

            context = {'active_id': active_id, 'active_ids': [active_id]}
            apm = self.env['sale.advance.payment.inv'].with_context(context).create({'advance_payment_method': 'all'})
            apm.create_invoices()

            invoice = self.env['account.invoice'].search([('origin', '=', sale.name)], limit=1)
            invoice.write({
                'it_type_document': sale.it_type_document.id,
                'serie_id': sale.it_invoice_serie.id
            })

            if warehouse_id.account_id:
                invoice.write({
                    'account_id': warehouse_id.account_id,
                })

            invoice.action_invoice_open()
            reference = invoice.reference
            # invoice = self.env['account.invoice'].browse(invoice.id)
            sale.write({
                'invoice_number': reference,
            })
