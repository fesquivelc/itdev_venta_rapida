# coding=utf-8
from odoo import fields, api, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    account_id = fields.Many2one('account.account', u'Cuenta de caja')
    tipo_doc_id = fields.Many2one('einvoice.catalog.01', u'Tipo de documento por defecto')
    invoice_serie_id = fields.Many2one('it.invoice.serie', u'Serie por defecto')
