from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string='Centro de Costo', check_company=True)
    
    """ @api.onchange('company_id') 
    def _onchange_company_id(self):
        # Aplicar un dominio al campo account_analytic_id basado en la compañía seleccionada
        domain = [('company_id', '=', self.company_id.id)]
        return {'domain': {'account_analytic_id': domain}} """
    
    @api.onchange('account_analytic_id')
    def _onchange_account_analytic_id(self):
        self.move_ids_without_package.account_analytic_id = self.account_analytic_id
    
    def stock_move_validate_account_analtic(self):
        stock_move_ids = self.move_ids_without_package
        # if self.picking_type_code == 'internal' and any(not move.account_analytic_id for move in stock_move_ids):
        #     raise ValidationError("No se ha seleccionado centro de costo para los movimientos")
        if self.location_id.usage == 'internal' and self.location_dest_id.usage == 'production' and any(not move.account_analytic_id for move in stock_move_ids):
            raise ValidationError("No se ha seleccionado centro de costo para los movimientos")
    def button_validate(self):
        self.stock_move_validate_account_analtic()
        res = super(StockPicking, self).button_validate()
        return res
        