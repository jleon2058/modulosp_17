from odoo import fields, models,api, _

# Muestra las facturas , generadas desde los ingresos , en la pantalla de la OC

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_view_account_move(self):

        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_journal_line"
        )

        action["context"] = {}
        line_order = self.mapped('order_line').ids
        line_account = self.env['account.move.line'].search([('purchase_line_id','in',line_order)]).move_id
        if len(line_account)>0:
            action["domain"]=[("id","in",line_account.ids)]
        return action