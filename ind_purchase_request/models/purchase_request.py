from odoo import models, fields,api

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    @api.depends('line_ids.request_state')
    def rechazar_requerimiento(self):
        for request in self:
            if all(req.request_state=='rejected' for req in request.line_ids):
                request.state='rejected'

    date_start = fields.Date(
        string="Creation date",
        help="Date when the user initiated the request.",
        default=fields.Date.context_today,
        tracking=True,
        readonly=True
    )

    approved_by = fields.Many2one(
        comodel_name ="res.users",
        string = "Aprobado por",
        readonly = "True",
        copy =False,
        tracking =True,
        index = True,
    )
    
    date_approved = fields.Datetime(
        string="Fecha de Aprobación",
        readonly = "True",
        copy = False,
        tracking = True,
        index = True,
    )

    def button_approved(self):
        """Acción para aprobar la solicitud"""
        for request in self:
            # Lógica de aprobación, por ejemplo cambiar el estado a 'approved'
            request.state = 'approved'
            # Asigna el usuario que aprueba y la fecha actual
            request.approved_by = self.env.user.id
            request.date_approved = fields.Datetime.now()

        return True