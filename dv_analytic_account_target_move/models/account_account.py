from odoo import api, fields, models, _


class AccountAccount(models.Model):
    _inherit = "account.account"
    
    is_analytic_account_required = fields.Boolean(string='Centro de costo requerido')
    
    account_target_move_type = fields.Selection([
        ('none', 'None'),
        ('entry', 'Journal entries'),
        ('analytic', 'Analytic accounts')
    ], string="Account Target Enries Type", default='none')
    
    debit_target_account_id = fields.Many2one('account.account', string='Cta. destino Debe')
    credit_target_account_id = fields.Many2one('account.account', string='Cta. detino Haber')
