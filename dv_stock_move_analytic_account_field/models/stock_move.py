from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    picking_type_code = fields.Selection(
        related='picking_type_id.code', store=True)
    
    def _default_account_analytic_id(self):
        account_analytic_id = False
        if 'default_picking_id' in self.env.context:
            picking_id = self.env['stock.picking'].browse(self.env.context['default_picking_id'])
            account_analytic_id = picking_id.account_analytic_id.id
        return account_analytic_id
    
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string='Centro de Costo', default=_default_account_analytic_id, check_company=True)
    
    """ @api.onchange('company_id') 
    def _onchange_company_id(self):
        # Aplicar un dominio al campo account_analytic_id basado en la compañía seleccionada
        domain = [('company_id', '=', self.company_id.id)]
        return {'domain': {'account_analytic_id': domain}} """

    def _prepare_common_svl_vals(self):
        res = super(StockMove, self)._prepare_common_svl_vals()
        res['account_analytic_id'] = self.account_analytic_id.id if self.account_analytic_id else False
        return res
    
    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        # Obtén la lista original de campos utilizando super()
        fields_list = super(StockMove, self)._prepare_merge_moves_distinct_fields()

        # Agrega tu campo adicional a la lista
        fields_list.append('account_analytic_id')

        return fields_list