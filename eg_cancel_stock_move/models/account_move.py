from odoo import api,fields,models

class AccountMove(models.Model):

    _inherit = 'account.move'

    def bulk_account_move_line_cancel(self):
        """this method used to sales order confirmation in bulk."""
        for account_move in self:
            if not self.env.user.has_group('base.group_system'):
                raise AccessError("Access Denegado")
            account_move.update({'state': 'cancel'})

    def bulk_account_move_line_cancel_reset(self):
        """this method used to sales order confirmation in bulk."""
        for account_move in self:
            if not self.env.user.has_group('base.group_system'):
                raise AccessError("Access Denegado")
            account_move.update({'state': 'draft'})