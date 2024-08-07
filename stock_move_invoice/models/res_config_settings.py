# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class Settings(models.TransientModel):
    """Inheriting model res.config.settings to add journal fields"""
    _inherit = 'res.config.settings'

    customer_journal_id = fields.Many2one('account.journal',
                                          string='Customer Journal',
                                          config_parameter=
                                          'stock_move_invoice.'
                                          'customer_journal_id',
                                          help='To add customer journal')
    vendor_journal_id = fields.Many2one('account.journal',
                                        string='Vendor Journal',
                                        config_parameter=
                                        'stock_move_invoice.vendor_journal_id',
                                        help='To add vendor journal')
