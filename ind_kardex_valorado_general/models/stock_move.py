from odoo import models,fields,api
from datetime import date
import logging
logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    asiento_id = fields.Integer(string="Id Asiento",compute="get_picking_id",store=True)
    monto_asiento = fields.Float(string="Monto del Asiento",compute="calcular_monto_asigned",store=True)
    precio_unit_asiento = fields.Float(string = "Precio Unitario Asientos" , compute="calcular_precio_unitario",store=True)


    @api.depends('account_move_ids')
    def get_picking_id(self):
        
        for record in self:
            if record.account_move_ids:
                primer_account_move=record.account_move_ids[0]
                record.asiento_id=primer_account_move.id
    
    @api.depends('account_move_ids',)
    def calcular_monto_asigned(self):
        for record in self:
            
            if record.location_dest_id.usage=='internal':
                if record.account_move_ids:
                    primer_account_move=record.account_move_ids[0]

                    asiento_monto=0

                    for line in primer_account_move.line_ids:
                        if line.account_id.account_type=='asset_current':
                            asiento_monto=asiento_monto+line.debit

                    record.monto_asiento=asiento_monto
            else:
                if record.account_move_ids:
                    primer_account_move=record.account_move_ids[0]

                    asiento_monto=0

                    for line in primer_account_move.line_ids:
                        if line.account_id.account_type=='asset_current':
                            asiento_monto=asiento_monto+line.credit

                    record.monto_asiento=asiento_monto

    @api.depends('monto_asiento', 'product_uom_qty')
    def calcular_precio_unitario(self):
        for record in self:
            if record.monto_asiento and record.product_uom_qty:
                record.precio_unit_asiento=round(record.monto_asiento/record.product_uom_qty,6)
            else:
                record.precio_unit_asiento = 0

    


    # @api.model
    # def _create_account_move(self,move):

    #     company = move.company_id

    #     self.env['account.move'].create()

    # def _action_done(self):

    #     res = super(StockMove,self)._action_done()
    #     for move in self:
    #         self._create_account_move(move)
    #     return res