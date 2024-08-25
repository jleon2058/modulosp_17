from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    is_analytic_account_required = fields.Boolean(related='account_id.is_analytic_account_required', store=True)
    account_target_move_type = fields.Selection(related='account_id.account_target_move_type', store=True)
    is_target_move_line = fields.Boolean(string='Es linea de destino', default=False, required=True)

    def validate_analytic_account(self):
        for line in self:    
            if line.is_analytic_account_required and not line.analytic_account_id:
                raise UserError(f'La cuenta contable {line.account_id.name} requiere un centro de costo.')
    def create(self, vals):
        res = super(AccountMoveLine, self).create(vals)
        res.validate_analytic_account()
        return res
    
    def _create_target_move_lines(self, debit_target_account_id, credit_target_account_id):
        self.ensure_one()
        line_data = {
            'name': self.name,
            'ref': self.name,
            'partner_id': self.partner_id and self.partner_id.id or False,
            'currency_id': self.currency_id and self.currency_id.id or False,
            'is_target_move_line': True,
        }
        debit_data = dict(line_data)
        credit_data = dict(line_data)

        if self.debit != False:
            debit_data.update(
                account_id=debit_target_account_id.id,
                debit=self.debit,
                credit=False,
                amount_currency=self.amount_currency,
            )
            credit_data.update(
                account_id=credit_target_account_id.id,
                debit=False,
                credit=self.debit,
                amount_currency=self.amount_currency * -1.0,
            )
        else:
            debit_data.update(
                account_id=debit_target_account_id.id,
                debit=False,
                credit=self.credit,
                amount_currency=self.amount_currency,
            )
            credit_data.update(
                account_id=credit_target_account_id.id,
                debit=self.credit,
                credit=False,
                amount_currency=self.amount_currency * -1.0,
            )
        self.move_id.line_ids = [(0, 0, debit_data), (0, 0, credit_data)]