# coding=utf-8
import logging
import pytz
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

ESTADO_CAJA = (
    ('borrador', 'Borrador'),
    ('abierto', 'Abierto'),
    ('cerrado', 'Cerrado')
)


class SaleCashbox(models.Model):
    _name = 'sale.cashbox.it'
    _order = 'fecha_apertura desc'

    name = fields.Char(u'Nombre', required=True, default='Borrador')
    state = fields.Selection(ESTADO_CAJA, u'Estado', required=True, default='borrador')
    fecha_apertura = fields.Datetime(u'Fecha de apertura')
    fecha_cierre = fields.Datetime(u'Fecha de cierre')
    sale_order_count = fields.Integer(compute='_count_sale_order')
    warehouse_id = fields.Many2one('stock.warehouse', string=u'Almacén', required=True)

    def _count_sale_order(self):
        conteo = self.env['sale.order'].search_count(
            [('cashbox_id', '=', self.id), ('state', 'in', ['done', 'sale', 'cancel'])])
        self.sale_order_count = conteo

    # @api.multi
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         fecha_apertura = record.fecha_apertura
    #         fecha_cierre = record.fecha_cierre
    #         name = record.name
    #         if fecha_apertura:
    #             name = "%s [%s / %s]" % (name, fecha_apertura, fecha_cierre or 'Actual')
    #         else:
    #             name = "[Borrador] %s" % name
    #         result.append((record.id, name))
    #     return result

    @api.multi
    def abrir_caja(self):
        self.ensure_one()
        # Buscamos una caja que este abierta
        cajas_abiertas = self.env['sale.cashbox.it'].search_count(
            [('state', '=', 'abierto'), ('warehouse_id', '=', self.warehouse_id.id)])

        if cajas_abiertas:
            raise ValidationError(_('¡Ya existe una arqueo de caja abierto actualmente!'))
        else:
            sequence = self.env['ir.sequence'].search([('code', '=', 'cashbox.sequence.it')], limit=1)
            if sequence.exists():
                self.write({
                    'fecha_apertura': datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'),
                    'state': 'abierto',
                    'name': sequence.next_by_id()
                })
            else:
                raise ValidationError(_('¡No existe una secuencia creada!'))

    @api.multi
    def cerrar_caja(self):
        self.ensure_one()
        self.write({
            'fecha_cierre': datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'state': 'cerrado'
        })
