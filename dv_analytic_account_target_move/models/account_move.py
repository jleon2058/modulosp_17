from odoo.exceptions import UserError
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        for move in self: #.filtered(lambda m: m.move_type not in ['out_invoice', 'out_receipt'])
            for line in move.line_ids:
                line.validate_analytic_account()
                if line.account_target_move_type == 'entry' and (line.debit + line.credit) != 0:
                    debit_target_account_id = line.account_id.debit_target_account_id
                    credit_target_account_id = line.account_id.credit_target_account_id
                    if not debit_target_account_id or not credit_target_account_id:
                        raise UserError(
                            _('Target accounts not found for: %s') % line.account_id.name)
                    line._create_target_move_lines(
                        debit_target_account_id, credit_target_account_id)
                elif line.account_target_move_type == 'analytic' and line.analytic_account_id and (line.debit + line.credit) != 0:
                    debit_target_account_id = line.analytic_account_id.debit_target_account_id
                    credit_target_account_id = line.analytic_account_id.credit_target_account_id
                    if debit_target_account_id and credit_target_account_id:
                        line._create_target_move_lines(
                        debit_target_account_id, credit_target_account_id)
        res = super(AccountMove, self)._post(soft=soft)
        return res

    def button_draft(self):
        super(AccountMove, self).button_draft()
        self.line_ids.filtered(lambda l: l.is_target_move_line).unlink()