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
    invoice_number = fields.Char(u'Número', store=True, readonly=False, required=True)
    account_journal = fields.Many2one('account.journal', u'Diario de pago', default=_get_account_journal,
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    einvoice_means_payment = fields.Many2one('einvoice.means.payment', u'Medio de pago',
                                             default=_get_einvoice_means_payment,
                                             states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    @api.onchange('warehouse_id', 'it_invoice_serie')
    def onchange_warehouse_id(self):
        for order in self:
            warehouse_id = order.warehouse_id
            tipo_doc_id = warehouse_id.tipo_doc_id
            serie_id = warehouse_id.invoice_serie_id
            if not serie_id:
                tipo_doc_id = order._get_tipo_documento()
                serie_id = order._get_serie()
            invoice_number = self.obtener_numero(serie_id)
            order.update({
                'it_type_document': tipo_doc_id,
                'it_invoice_serie': serie_id,
                'invoice_number': invoice_number
            })

            # order.it_type_document = tipo_doc_id
            # order.it_invoice_serie = serie_id
            # order.invoice_number = self.obtener_numero(serie_id)

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if not vals.get('invoice_number', False):
            serie_id = self.env['it.invoice.serie'].browse(vals.get('it_invoice_serie'))
            vals.update({'invoice_number': self.obtener_numero(serie_id)})
        return super(SaleOrder, self).create(vals)

    def obtener_numero(self, serie_id):

        sequence_id = serie_id.sequence_id
        padding = sequence_id.padding
        prefix = sequence_id.prefix
        numero = sequence_id.number_next
        siguiente = '%s%0{}d'.format(padding) % (prefix, numero)
        return siguiente

    @api.onchange('doc_search')
    def onchange_doc_search(self):
        partner = self.env['res.partner'].search([('nro_documento', '=', self.doc_search)], limit=1)
        if partner.exists():
            return {
                'value': {'partner_id': partner.id}
            }
        else:
            raise UserError(_('Cliente no encontrado'))
