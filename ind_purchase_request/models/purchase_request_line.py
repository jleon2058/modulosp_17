from odoo import _,models,fields,api
from odoo.exceptions import UserError

class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    request_state = fields.Selection(
        string="Request state",
        related="request_id.state",
        store=True,
    )

    estimated_cost = fields.Float(related='product_id.standard_price')

    approved_by = fields.Many2one(
        comodel_name="res.users",
        related="request_id.approved_by",
        string="Aprobado por",
        store=True,
        readonly=True,
    )
    
    date_approved = fields.Datetime(
        related="request_id.date_approved",
        string="Fecha de Aprobación",
        store=True,
        readonly=True
    )

    def write(self,vals):
        result = super(PurchaseRequestLine,self).write(vals)
        if 'request_state' in vals:
            self.mapped('request_id').rechazar_requerimiento()
        return result

    def rechazar_request_line(self):
        for record in self:
            if record.request_state == 'approved':
                record.request_state='rejected'
            else:
                raise UserError(_("Purchase Requeste {} with item {} is not approved").format(record.request_id.name,record.name))
        return True

    def rechazar_multiple_request_line(self):
        for record in self:
            record.rechazar_request_line()
        return {
            'type':'ir.actions.act_window_close'
        }