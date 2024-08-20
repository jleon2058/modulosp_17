from odoo import api, fields, models, _


class StockValuationLayer(models.Model):
	_inherit = 'stock.valuation.layer'

	account_analytic_id = fields.Many2one('account.analytic.account', string='Centro de Costo')
