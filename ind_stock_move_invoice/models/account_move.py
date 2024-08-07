from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    transfer_ids = fields.Many2many(
            comodel_name='stock.picking',
            relation='account_move_stock_picking_rel',
            column1='account_move_id',
            column2='stock_picking_id',
            string='Transfers'
            )