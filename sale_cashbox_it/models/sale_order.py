# coding=utf-8
import logging
import pytz
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_cashbox_abierto(self):
        cashbox_id = self.env['sale.cashbox.it'].search([('state', '=', 'abierto')], limit=1)
        if cashbox_id.exists():
            return cashbox_id.id

    cashbox_id = fields.Many2one('sale.cashbox.it', u'Arqueo de caja', default=_get_cashbox_abierto)

    @api.constrains('cashbox_id')
    def check_cashbox_id(self):
        if not self.cashbox_id:
            raise ValidationError(_('¡Debe existir un arqueo de caja!'))

    @api.onchange('cashbox_id')
    def select_cashbox_id(self):
        self.ensure_one()
        self.update({
            'warehouse_id': self.cashbox_id.warehouse_id.id
        })
