# coding=utf-8
import logging
import pytz
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_tipo_documento(self):
        param = self.env['sale.parameters.it'].search([])
        if param.type_document_id:
            return param.type_document_id.id

    def _get_serie(self):
        param = self.env['sale.parameters.it'].search([])
        if param.invoice_serie_id:
            return param.invoice_serie_id.id

    def _get_account_journal(self):
        param = self.env['sale.parameters.it'].search([])
        if param.account_journal_id:
            return param.account_journal_id.id

    def _get_einvoice_means_payment(self):
        param = self.env['sale.parameters.it'].search([])
        if param.means_payment_id:
            return param.means_payment_id.id

    def _get_partner_id(self):
        param = self.env['main.parameter'].search([])
        if param.partner_venta_boleta:
            return param.partner_venta_boleta.id

    doc_search = fields.Char(u'Buscar x nro documento')
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True,
                                 change_default=True, index=True, track_visibility='always', default=_get_partner_id)
    it_type_document = fields.Many2one('einvoice.catalog.01', u'Tipo de documento',
                                       states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    it_invoice_serie = fields.Many2one('it.invoice.serie', u'Serie',
                                       states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    sequence_id = fields.Many2one('ir.sequence', related='it_invoice_serie.sequence_id')
    invoice_number = fields.Char(u'Número')
    account_journal = fields.Many2one('account.journal', u'Diario de pago', default=_get_account_journal,
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    einvoice_means_payment = fields.Many2one('einvoice.means.payment', u'Medio de pago',
                                             default=_get_einvoice_means_payment,
                                             states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        warehouse_id = self.warehouse_id
        tipo_doc_id = warehouse_id.tipo_doc_id
        serie_id = warehouse_id.invoice_serie_id
        if not serie_id:
            tipo_doc_id = self._get_tipo_documento()
            serie_id = self._get_serie()
        self.it_type_document = tipo_doc_id
        self.it_invoice_serie = serie_id
        self.obtener_numero()



    @api.onchange('it_invoice_serie')
    def obtener_numero(self):
        padding = self.sequence_id.padding
        prefix = self.sequence_id.prefix
        numero = self.sequence_id.number_next
        siguiente = '%s%0{}d'.format(padding) % (prefix, numero)
        self.invoice_number = siguiente

    @api.onchange('doc_search')
    def onchange_doc_search(self):
        partner = self.env['res.partner'].search([('nro_documento', '=', self.doc_search)], limit=1)
        if partner.exists():
            return {
                'value': {'partner_id': partner.id}
            }
        else:
            raise UserError(_('Cliente no encontrado'))
