# coding=utf-8
import logging
import pytz
from datetime import datetime
import odoo.addons.decimal_precision as dp

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

SEARCH_TIPO = (
    ('categoria', u'Por categoría'),
    ('codigo', u'Por código'),
    ('descripcion', u'Descripción'),
)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    search_codigo = fields.Char(u'Código')
    search_box = fields.Char(u'Buscar')
    search_categ_id = fields.Many2one('product.category', u'Categoría')
    search_tipo = fields.Selection(SEARCH_TIPO, u'Opciones', default='descripcion')
    search_line_ids = fields.One2many('sale.search.line', 'order_id')
    search_completa = fields.Boolean(u'Búsqueda completa', default=False)

    @api.multi
    def buscar(self):
        self.search_line_ids = [(6, 0, [])]
        busqueda = self.search_box and self.search_box.strip() or False
        condicion = []
        conteo = 0
        if self.search_codigo and self.search_codigo.strip():
            if not self.search_completa:
                condicion = condicion + ['|', ('default_code', '=', self.search_codigo),
                                         ('barcode', '=', self.search_codigo)]
            else:
                condicion = condicion + ['|', ('default_code', '=ilike', '%{}%'.format(self.search_codigo or '---')),
                                         ('barcode', '=ilike', '%{}%'.format(self.search_codigo.strip() or '---'))]
            conteo += 1

        if self.search_categ_id:
            if not busqueda:
                raise ValidationError(u'Para la búsqueda por categoría debe escribir en la caja de descripción')
            condicion = condicion + [('categ_id', '=', self.search_categ_id.id)]
            conteo += 1

        if busqueda:
            condicion = condicion + [('name', '=ilike', '{}{}%'.format(self.search_completa and '%' or '', busqueda))]
            conteo += 1

        if conteo > 1:
            condicion = ['&' for i in range(conteo - 1)] + condicion

        product_ids = self.env['product.product'].search(condicion)
        if product_ids.exists():
            self._generar_lineas_busqueda(product_ids)

    def _generar_lineas_busqueda(self, product_ids):
        ids = product_ids.ids
        saldo = self.get_saldo()

        lineas = [(0, False, {
            'product_id': product.id,
            'product_qty': 0,

        }) for product in product_ids]
        self.search_line_ids = lineas
        self._actualizar_lineas_busqueda()

    def _actualizar_lineas_busqueda(self):
        for line in self.search_line_ids:
            line.write({'pricelist_id': self.pricelist_id.id})
            line.onchange_pricelist_id()

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        self._actualizar_lineas_busqueda()

    @api.multi
    def agregar_lineas_compra(self):
        seq = 10
        order_lines = []
        if self.search_line_ids:
            for line in self.search_line_ids:
                if line and line.product_qty > 0:
                    order_lines.append((0, False, {
                        u'qty_delivered': 0,
                        u'product_id': line.product_id.id,
                        u'product_uom': line.product_id.uom_id,
                        u'sequence': seq,
                        u'price_unit': line.price_unit,
                        u'product_uom_qty': line.product_qty,
                        u'name': line.product_id.name
                    }))
                seq = seq + 10
        if order_lines:
            self.order_line = order_lines
            self.search_line_ids = [(6, 0, [])]
            self.search_codigo = False
            self.search_box = False
            self.search_categ_id = False
            self.search_tipo = False
            self.search_completa = False
        else:
            raise ValidationError(_('No hay productos para agregar'))

    @api.multi
    def saldo_search(self, product_ids):
        # self.rebuild_kardex()
        self.env['detalle.simple.fisico.total.d'].search([('producto', 'in', product_ids)])

    @api.multi
    def rebuild_kardex(self):
        year = datetime.utcnow().year
        fiscal_year = self.env['account.fiscalyear'].search([('name', '=', str(year))])
        saldos = self.env['detalle.simple.fisico.total.d.wizard'].create({'fiscalyear_id': fiscal_year.id})
        saldos.do_rebuild()


class SaleOrderSearchLine(models.Model):
    _name = 'sale.search.line'

    order_id = fields.Many2one('sale.order')
    product_id = fields.Many2one('product.product', u'Producto')
    product_code = fields.Char(u'Código', related='product_id.default_code')
    uom_id = fields.Many2one('product.uom', related='product_id.unidad_kardex')
    pricelist_id = fields.Many2one('product.pricelist')
    pricelist_currency = fields.Many2one('res.currency', related='pricelist_id.currency_id', string='Moneda')
    price_unit = fields.Float('Precio unit.', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    product_min_qty = fields.Float(string='Cantidad min.')
    product_qty = fields.Float(string='Cantidad', digits=dp.get_precision('Product Unit of Measure'), required=True,
                               default=1.0)
    product_hand_qty = fields.Float(string='Cantidad a mano', digits=dp.get_precision('Product Unit of Measure'),
                                    default=1.0, compute='_compute_cantidad_mano')

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        price_unit = False
        product_min_qty = False
        if self.product_id and self.pricelist_id:
            filtro = self.pricelist_id.item_ids.filtered(lambda i:
                                                         i.product_id.id == self.product_id.id or
                                                         i.product_tmpl_id.id == self.product_id.product_tmpl_id.id)
            if filtro.exists():
                price_unit = filtro[0].fixed_price
                product_min_qty = filtro[0].min_quantity
        if not price_unit:
            price_unit = self.product_id.list_price
        self.price_unit = price_unit
        self.product_min_qty = product_min_qty

    def _compute_cantidad_mano(self):
        for line in self:
            cantidad = False
            res = self.env['detalle.simple.fisico.total.d'].search([('producto', '=', line.product_id.id)])
            if res.exists():
                cantidad = sum(res.mapped('saldo'))
            line.product_hand_qty = cantidad

    # @api.depends('product_id', 'pricelist_id')
    # def _compute_pricelist(self):
    #     price_unit = False
    #     product_min_qty = False
    #     if self.product_id and self.pricelist_id:
    #
    #         filtro = self.pricelist_id.item_ids.filter(lambda i: i.product_id.id == self.product_id.id)
    #         if filtro:
    #             price_unit = filtro[0].fixed_price
    #     if not price_unit:
    #         price_unit = self.product_id.list_price
    #     self.price_unit = price_unit
    #     self.product_min_qty = product_min_qty
