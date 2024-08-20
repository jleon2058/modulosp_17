from odoo import models,fields

class UnidadMedida(models.Model):
    _inherit = 'uom.uom'

    codigo_sunat = fields.Char(string="Codigo Sunat")