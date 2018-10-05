# coding=utf-8
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleConfiguration(models.Model):
    _name = 'sale.parameters.it'

    # @api.model_cr
    # def init(self):
    #     conteo = self.env['sale.parameters.it'].search_count([])
    #     if conteo == 0:
    #         self.env['sale.parameters.it'].sudo().create({'name': u'Parámetros de venta'})

    name = fields.Char('Nombre', size=50, default=u'Parámetros de venta')
    payment_term_id = fields.Many2one('account.payment.term', string=u'Plazo de pago por defecto')
    type_document_id = fields.Many2one('einvoice.catalog.01', u'Tipo de documento por defecto')
    invoice_serie_id = fields.Many2one('it.invoice.serie', u'Serie por defecto')
    account_journal_id = fields.Many2one('account.journal', u'Diario de pago x defecto')
    means_payment_id = fields.Many2one('einvoice.means.payment', u'Diario de pago x defecto')
    force_assign = fields.Boolean(u'Forzar asignación en el albarán', default=False)
