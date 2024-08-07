from odoo import fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    account_move_line_ids = fields.One2many(
                    comodel_name = "account.move.line",
                    inverse_name = "stock_move_id",
                    string = "lineas de asiento",
                    ondelete='cascade'
                    )
