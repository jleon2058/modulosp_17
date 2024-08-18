from odoo import fields, models,api, _
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    account_move_ids = fields.Many2many(
            comodel_name='account.move',
            relation='account_move_stock_picking_rel',
            column1='stock_picking_id',
            column2='account_move_id',
            string='Factura',
            readonly=True
            )
    
    # account_move_id=fields.Integer(string="Id Factura",compute="get_account_move_id",store=True)

    # @api.depends('account_move_ids')
    # def get_account_move_id(self):
        
    #     for record in self:
    #         if record.account_move_ids:
    #             primer_account_move=record.account_move_ids[0]
    #             record.account_move_id=primer_account_move.id
    
    def _compute_invoice_count(self):
        """This compute function used to count the number of invoice for the picking"""
        for picking_id in self:
            # move_ids = picking_id.env['account.move'].search([('invoice_origin', '=', picking_id.name)])
            move_ids = picking_id.env['account.move'].search([('transfer_ids', 'in', picking_id.id)])
            if move_ids:
                self.invoice_count = len(move_ids)
            else:
                self.invoice_count = 0
        
    def action_create_bill(self):
        """This is the function for creating vendor bill
                from the picking"""
        for picking_id in self:
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'incoming':
                vendor_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.vendor_journal_id') or False
                if not vendor_journal_id:
                    raise UserError(_("Please configure the journal from the settings."))
                invoice_line_list = []
                for move_ids_without_package in picking_id.move_ids_without_package:
                    if move_ids_without_package.account_move_line_ids:
                        total_quantity = sum(line.quantity for line in move_ids_without_package.account_move_line_ids.filtered(lambda x: x.parent_state == 'posted'))
                        pendiente_quantity = move_ids_without_package.quantity - total_quantity
                    else:                       
                        pendiente_quantity = move_ids_without_package.quantity
                    if pendiente_quantity>0:
                        vals = (0, 0, {
                            'name': move_ids_without_package.description_picking,
                            'product_id': move_ids_without_package.product_id.id,
                            # 'price_unit': move_ids_without_package.product_id.lst_price,
                            'price_unit': move_ids_without_package.purchase_line_id.price_unit,
                            'product_uom_id': move_ids_without_package.purchase_line_id.product_uom.id,
                            'account_id': move_ids_without_package.product_id.property_account_expense_id.id if move_ids_without_package.product_id.property_account_expense_id
                            else move_ids_without_package.product_id.categ_id.property_account_expense_categ_id.id,
                            # 'tax_ids': [(6, 0, [picking_id.company_id.account_purchase_tax_id.id])],
                            'discount': move_ids_without_package.purchase_line_id.discount,
                            'tax_ids': [(6, 0, [move_ids_without_package.purchase_line_id.taxes_id.id])],
                            'quantity': pendiente_quantity,
                            'purchase_line_id': move_ids_without_package.purchase_line_id.id,
                            'stock_move_id': move_ids_without_package.id
                        })
                        if move_ids_without_package.purchase_line_id.analytic_distribution and not move_ids_without_package.purchase_line_id.display_type:
                            vals[2]['analytic_distribution'] = move_ids_without_package.purchase_line_id.analytic_distribution
                        invoice_line_list.append(vals)
                invoice = picking_id.env['account.move'].create({
                    'move_type': 'in_invoice',
                    'invoice_origin': picking_id.name,
                    'invoice_user_id': current_user,
                    'narration': picking_id.name,
                    'partner_id': picking_id.partner_id.id,
                    # 'currency_id': picking_id.env.user.company_id.currency_id.id,
                    'currency_id': picking_id.purchase_id.currency_id.id,
                    'journal_id': int(vendor_journal_id),
                    'payment_reference': picking_id.name,
                    'picking_id': picking_id.id,
                    'invoice_line_ids': invoice_line_list,
                    'transfer_ids': self,
                    'invoice_payment_term_id':picking_id.purchase_id.payment_term_id.id
                })
                return invoice


    def action_open_picking_invoice(self):
        """This is the function of the smart button which redirect to the
        invoice related to the current picking"""
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            # 'domain': [('invoice_origin', '=', self.name)],
            'domain': [('transfer_ids', 'in', self.id)],
            'context': {'create': False},
            'target': 'current'
        }
       
        
    def action_create_multi_invoice_for_multi_transfer(self):
        picking_type = list(self.picking_type_id)
        picking_idss = list(self)
        logger.warning("----lista-------")
        logger.warning(picking_idss)
        if all(first.state=='done' for first in picking_idss):
        #if all((first == picking_type[0] or first != picking_type[0]) for first in picking_type):
            # if self.picking_type_id.code == 'outgoing':
            if all(first.code == 'outgoing' for first in picking_type):
                logger.warning("--------outgoing-------")
                partner = list(self.partner_id)
                if all(first == partner[0] for first in partner):
                    partner_id = self.partner_id
                    invoice_line_list = []
                    customer_journal_id = \
                        self.env['ir.config_parameter'].sudo().\
                            get_param('stock_move_invoice.customer_journal_id') \
                        or False
                    if not customer_journal_id:
                        raise UserError(
                            _("Please configure the journal from settings"))
                    for picking_id in self:
                        for move_ids_without_package in picking_id.\
                                move_ids_without_package:
                            if move_ids_without_package.state=='done':
                                if move_ids_without_package.account_move_line_ids:
                                    total_quantity = sum(line.quantity for line in move_ids_without_package.account_move_line_ids.filtered(lambda x: x.parent_state == 'posted'))
                                    pendiente_quantity = move_ids_without_package.quantity - total_quantity
                                else:
                                    pendiente_quantity=move_ids_without_package.quantity
                                if pendiente_quantity>0:
                                    vals = (0, 0, {
                                        'name':
                                            move_ids_without_package.description_picking
                                        ,
                                        'product_id':
                                            move_ids_without_package.product_id.id,
                                        # 'price_unit': move_ids_without_package.
                                        #     product_id.lst_price,
                                        'price_unit': move_ids_without_package.purchase_line_id.price_unit,
                                        #'product_uom_id': move_ids_without_package.purchase_line_id.product_uom,
                                        'product_uom_id': move_ids_without_package.purchase_line_id.product_uom.id,
                                        'account_id': move_ids_without_package.product_id.property_account_expense_id.id if move_ids_without_package.product_id.property_account_expense_id
                                        else move_ids_without_package.product_id.categ_id.property_account_expense_categ_id.id,
                                        # 'tax_ids': [(6, 0, [picking_id.company_id.
                                        #              account_purchase_tax_id.id])],
                                        'discount': move_ids_without_package.purchase_line_id.discount,
                                        'tax_ids': [(6, 0, [move_ids_without_package.purchase_line_id.taxes_id.id])],
                                        'quantity':
                                            pendiente_quantity,
                                        'purchase_line_id': move_ids_without_package.purchase_line_id.id,
                                        'stock_move_id': move_ids_without_package.id
                                    })
                                    if move_ids_without_package.purchase_line_id.analytic_distribution and not move_ids_without_package.purchase_line_id.display_type:
                                        vals[2]['analytic_distribution'] = move_ids_without_package.purchase_line_id.analytic_distribution
                                    invoice_line_list.append(vals)
                    invoice = self.env['account.move'].create({
                        'move_type': 'out_invoice',
                        'invoice_origin': picking_id.name,
                        'invoice_user_id': self.env.uid,
                        'narration': picking_id.name,
                        'partner_id': partner_id.id,
                        # 'currency_id':
                        #     picking_id.env.user.company_id.currency_id.id,
                        'currency_id': picking_id.purchase_id.currency_id.id,
                        'journal_id': int(customer_journal_id),
                        'payment_reference': picking_id.name,
                        'invoice_line_ids': invoice_line_list,
                        'transfer_ids': self,
                        'invoice_payment_term_id':picking_id.purchase_id.payment_term_id.id
                    })
                else:
                    for picking_id in self:
                        picking_id.create_invoice()
            elif all(first.code == 'incoming' for first in picking_type):
            #elif self.picking_type_id.code == 'incoming':
                logger.warning("--------incoming-------")
                partner = list(self.partner_id)
                if all(first == partner[0] for first in partner):
                    partner_id = self.partner_id
                    bill_line_list = []
                    vendor_journal_id = \
                        self.env['ir.config_parameter'].sudo().\
                            get_param('stock_move_invoice.vendor_journal_id') \
                        or False
                    if not vendor_journal_id:
                        raise UserError(_("Please configure the journal from "
                                            "the settings."))
                    for picking_id in self:
                        for move_ids_without_package in picking_id.\
                                move_ids_without_package:
                            if move_ids_without_package.state=='done':
                                if move_ids_without_package.account_move_line_ids:
                                    total_quantity = sum(line.quantity for line in move_ids_without_package.account_move_line_ids.filtered(lambda x: x.parent_state == 'posted'))
                                    pendiente_quantity = move_ids_without_package.quantity - total_quantity
                                else:
                                    pendiente_quantity=move_ids_without_package.quantity
                                if pendiente_quantity>0:

                                    vals = (0, 0, {
                                        'name':
                                            move_ids_without_package.description_picking
                                        ,
                                        'product_id':
                                            move_ids_without_package.product_id.id,
                                        # 'price_unit': move_ids_without_package.
                                        #     product_id.lst_price,
                                        'price_unit': move_ids_without_package.purchase_line_id.price_unit,
                                        #'product_uom_id': move_ids_without_package.purchase_line_id.product_uom,
                                        'product_uom_id': move_ids_without_package.purchase_line_id.product_uom.id,
                                        'account_id': move_ids_without_package.
                                            product_id.property_account_expense_id.id if
                                        move_ids_without_package.product_id.
                                            property_account_expense_id
                                        else move_ids_without_package.
                                            product_id.categ_id.
                                            property_account_expense_categ_id.id,
                                        # 'tax_ids': [(6, 0, [picking_id.company_id.
                                        #              account_purchase_tax_id.id])],
                                        'discount': move_ids_without_package.purchase_line_id.discount,
                                        'tax_ids': [(6, 0, [move_ids_without_package.purchase_line_id.taxes_id.id])],
                                        'quantity':
                                            pendiente_quantity,
                                        'purchase_line_id': move_ids_without_package.purchase_line_id.id,
                                        'stock_move_id': move_ids_without_package.id
                                    })
                                    if move_ids_without_package.purchase_line_id.analytic_distribution and not move_ids_without_package.purchase_line_id.display_type:
                                        vals[2]['analytic_distribution'] = move_ids_without_package.purchase_line_id.analytic_distribution
                                    bill_line_list.append(vals)

                    invoice = self.env['account.move'].create({
                        'move_type': 'in_invoice',
                        'invoice_origin': picking_id.name,
                        'invoice_user_id': self.env.uid,
                        'narration': picking_id.name,
                        'partner_id': partner_id.id,
                        # 'currency_id':
                        #     picking_id.env.user.company_id.currency_id.id,
                        'currency_id': picking_id.purchase_id.currency_id.id,
                        'journal_id': int(vendor_journal_id),
                        'payment_reference': picking_id.name,
                        'picking_id': picking_id.id,
                        'invoice_line_ids': bill_line_list,
                        'transfer_ids': self,
                        'invoice_payment_term_id':picking_id.purchase_id.payment_term_id.id
                    })
                else:
                    for picking_id in self:
                        picking_id.action_create_bill()
        else:
            raise UserError(
                _("Please select single type transfer"))