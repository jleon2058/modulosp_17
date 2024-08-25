from odoo import _,models,fields,api
from odoo.exceptions import UserError

class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    @api.model
    def _check_valid_request_line(self, request_line_ids):
        picking_type = False
        company_id = False
        print("--------_check_valid_request_lin-------")
        print(request_line_ids)
        for line in self.env["purchase.request.line"].browse(request_line_ids):
            if line.request_state == "done":
                raise UserError(_("The purchase has already been completed."))
            if line.request_state != "approved":
                print("--------_check_valid_request_lin-------")
                raise UserError(
                    #_("Purchase Request %s is not approved") % line.request_id.name
                    _("Purchase Requeste {} with item {} is not approved").format(line.request_id.name,line.name)
                )

            if line.purchase_state == "done":
                raise UserError(_("The purchase has already been completed."))

            line_company_id = line.company_id and line.company_id.id or False
            if company_id is not False and line_company_id != company_id:
                raise UserError(_("You have to select lines from the same company."))
            else:
                company_id = line_company_id

            line_picking_type = line.request_id.picking_type_id or False
            if not line_picking_type:
                raise UserError(_("You have to enter a Picking Type."))
            if picking_type is not False and line_picking_type != picking_type:
                raise UserError(
                    _("You have to select lines from the same Picking Type.")
                )
            else:
                picking_type = line_picking_type