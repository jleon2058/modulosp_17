# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.exceptions import UserError
from odoo.tools import (
    date_utils,
    email_re,
    email_split,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    groupby,
    index_exists,
    is_html_empty,
    create_index,
)
import logging
logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def product_price_update_before_done(self, forced_qty=None, is_new=False):
        """
        Update and check the standard_price of products before a validate picking or a new invoice entry.

        :param str|date forced_qty: new quantity
        :param str|date is_new: is a new calculation or a update a old calculation
        """
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}

        for move in self.filtered(lambda move: move._is_in() and move.with_company(move.company_id).product_id.cost_method == 'average'):

            product_tot_qty_available = move.product_id.sudo().with_company(move.company_id).quantity_svl + tmpl_dict[move.product_id.id]
            rounding = move.product_id.uom_id.rounding

            valued_move_lines = move._get_in_move_lines()
            # logger.warning("-------valued_move_lines-------")
            # logger.warning(valued_move_lines)
            quantity = 0
            for valued_move_line in valued_move_lines:
                quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.quantity, move.product_id.uom_id)
                # logger.warning("-------_compute_quantity-------")
                # logger.warning(valued_move_line.qty_done)
                # logger.warning(move.product_id.uom_id)

            qty = forced_qty or quantity
            # logger.warning("-------forced_qty or qty_done-------")
            # logger.warning(forced_qty)
            # logger.warning(qty_done)
            if float_is_zero(product_tot_qty_available, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            elif float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding) or \
                    float_is_zero(product_tot_qty_available + qty, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            else:
                # Get the standard price
                if is_new:
                    self.env.cr.execute(
                        """
                        SELECT sum(value), sum(quantity)_compute_quantity
                        FROM stock_valuation_layer WHERE company_id = {} and stock_move_id != {} and product_id = {}
                        """.format(move.company_id.id, move.id, move.product_id.id))
                    res = self.env.cr.fetchone()
                    new_std_price = ((res[0] or 0) + (move._get_price_unit() * abs(qty))) / ((res[1] or 0) + abs(qty))
                    # logger.warning("-------new_std_price------")
                    # logger.warning(new_std_price)
                    # logger.warning(move._get_price_unit() * abs(qty))

                else:
                    amount_unit = std_price_update.get((move.company_id.id, move.product_id.id)) or move.product_id.with_company(move.company_id).standard_price
                    new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (product_tot_qty_available + qty)
                    # logger.warning("------amount_unit-----")
                    # logger.warning(std_price_update.get((move.company_id.id, move.product_id.id)))
                    # logger.warning(move.product_id.with_company(move.company_id).standard_price)
                    # logger.warning("------new_std_price-----")
                    # logger.warning(amount_unit)
                    # logger.warning(new_std_price)
            tmpl_dict[move.product_id.id] += quantity
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_company(move.company_id.id).with_context(disable_auto_svl=True).sudo().write({'standard_price': new_std_price})
            std_price_update[move.company_id.id, move.product_id.id] = new_std_price

        # adapt standard price on incomming moves if the product cost_method is 'fifo'
        for move in self.filtered(lambda move:
                                  move.with_company(move.company_id).product_id.cost_method == 'fifo'
                                  and float_is_zero(move.product_id.sudo().quantity_svl, precision_rounding=move.product_id.uom_id.rounding)):
            move.product_id.with_company(move.company_id.id).sudo().write({'standard_price': move._get_price_unit()})

        # raise UserError("¡Hubo un error! La condición no se cumplió.")
    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        self.ensure_one()
        if self.purchase_line_id.order_id.currency_id.id != self.purchase_line_id.order_id.company_id.currency_id.id:
            if self.purchase_line_id and self.purchase_line_id.invoice_lines.filtered(lambda x: x.move_id.state not in ('draft', 'cancel')) and self.product_id.id == self.purchase_line_id.product_id.id:
                price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
                line = self.purchase_line_id.invoice_lines.filtered(lambda x: x.move_id.state not in ('draft', 'cancel'))[0]
                if line:
                    order = line.move_id #invoice
                    price_unit = line.price_unit #invoice
                    if line.tax_ids:
                        qty = line.quantity or 1
                        price_unit = line.tax_ids.with_context(round=False).compute_all(price_unit, currency=order.currency_id, quantity=qty)['total_void']
                        price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
                    if line.product_uom_id.id != line.product_id.uom_id.id:
                        price_unit *= line.product_uom_id.factor / line.product_id.uom_id.factor
                    if order.currency_id != order.company_id.currency_id:
                        # The date must be today, and not the date of the move since the move move is still
                        # in assigned state. However, the move date is the scheduled date until move is
                        # done, then date of actual move processing. See:
                        # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
                        price_unit = order.currency_id._convert(
                            price_unit, order.company_id.currency_id, order.company_id, order.date, round=False)
                    return price_unit
        return super(StockMove, self)._get_price_unit()

    def _get_avg_sql_price_unit(self):
        """ Returns the unit price for the move"""
        if self.purchase_line_id:
            return self._get_price_unit()
        self.env.cr.execute(
            """
            SELECT sum(value), sum(quantity)
            FROM stock_valuation_layer 
            WHERE company_id = {} and stock_move_id != {} and product_id = {} and create_date < '{}'""".format(self.company_id.id, self.id, self.product_id.id, self.date))
        res = self.env.cr.fetchone()
        return (res[0] or 0) / (res[1] or 1)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def cron_update_standard_price(self, start_date=None, end_date=None, invoice_ids=None):
        """
        Update standard_price of products.

        :param str|date start_date: start date of search params
        :param str|date end_date: end date of search params
        :param list invoice_ids: list of ids of invoices
        """
        if invoice_ids:
            return self.browse(invoice_ids).update_standard_price()
        params = []
        if start_date:
            params.append(('invoice_date', '>=', start_date))
        if end_date:
            params.append(('invoice_date', '<=', end_date))
        self.search(params).update_standard_price()

    def update_stock_move_line(self, line):
        valuation = self.env['stock.valuation.layer'].search([('stock_move_id', '=', line.id)])
        if valuation:
            unit_price = line._get_avg_sql_price_unit()
            valued_move_lines = line._get_in_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.quantity, line.product_id.uom_id)
            for i in valuation:
                i.write({
                    'value': line.company_id.currency_id.round(unit_price * i.quantity),
                    'unit_cost': unit_price,
                })
            for move in self.env['account.move'].search([('stock_move_id', '=', line.id)]):
                move.button_draft()
                move.line_ids.unlink()
                value_valuation = sum([v.value for v in valuation]) / len(valuation)
                vals = line._account_entry_move(valuation[0].quantity, valuation[0].description, valuation[0].id, value_valuation)[0]
                vals['date'] = move.date
                move.write(vals)
                move._post()
                if valuation.company_id.anglo_saxon_accounting:
                    valuation.stock_move_id._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=valuation.product_id)

    def update_standard_price(self):
        """
        Calculate new standard_price of products of the related purchase order
    ====================

    Legend:
        product = The REPL main loop stop.
        product_standard_price = Exception raised.
        account_move = Stay in REPL.
        ######1 = Account of chart account.
        ######2 = Account of chart account.

-------------------------TIME 0---------------------------
product_standard_price = old product_standard_price # we use the same value
F.E:

product_standard_price = S/. 100.00

 account  | debit      | credit     |
 ######1  | S/. 100.00 | 0          |
 ######2  | 0          | S/. 100.00 |

stock.valuation.layer
- current_date | S/. 100.00
-----------------------------------------------------------
-------------------------TIME 1---------------------------
account.move().update_standard_price
product_standard_price = new product_standard_price
F.E:

product_standard_price = S/. 110.00

 account  | debit      | credit     |
 ######1  | S/. 110.00 | 0          |
 ######2  | 0          | S/. 110.00 |

stock.valuation.layer
- current_date | S/. 110.00
-----------------------------------------------------------
        """
        line_ids = self.mapped('line_ids').mapped('purchase_line_id').ids
        move_lines = self.env['stock.move'].search([('purchase_line_id', 'in', line_ids)])

        # line_ids = self.mapped('picking_id').id
        # move_lines = self.env['stock.move'].search([('picking_id','=',line_ids)])

        for line in move_lines:
            line.product_price_update_before_done(
                forced_qty=sum(
                    [valued_move_line.product_uom_id._compute_quantity(valued_move_line.quantity, line.product_id.uom_id)
                     for valued_move_line in line._get_in_move_lines()]) * -1,
                is_new=True,
            )
            self.update_stock_move_line(line)
        if move_lines:
            for line in self.env['stock.move'].search([
                ('product_id', 'in', move_lines.mapped('product_id').ids),
                ('purchase_line_id', '=', False),
                ('date', '>=', move_lines[0].date),
                ('id', 'not in', move_lines.ids)
            ]):
                self.update_stock_move_line(line)
            move_lines[-1].product_price_update_before_done(
                forced_qty=sum(
                    [valued_move_line.product_uom_id._compute_quantity(valued_move_line.quantity, line.product_id.uom_id)
                     for valued_move_line in line._get_in_move_lines()]) * -1,
                is_new=True,
            )

    def action_post(self):
        """
        Function to process an account.move and recalculate the standard_price of products.
        """
        res = super(AccountMove, self).action_post()
        self.filtered(lambda x: x.currency_id.id != x.company_id.currency_id.id).update_standard_price()

        return res

    def _post(self, soft=True):
        """Post/Validate the documents.

        Posting the documents will give it a number, and check that the document is
        complete (some fields might not be required if not posted but are required
        otherwise).
        If the journal is locked with a hash table, it will be impossible to change
        some fields afterwards.

        :param soft (bool): if True, future documents are not immediately posted,
            but are set to be auto posted automatically at the set accounting date.
            Nothing will be performed on those documents before the accounting date.
        :return Model<account.move>: the documents that have been posted
        """
        if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
            raise AccessError(_("You don't have the access rights to post an invoice."))

        for invoice in self.filtered(lambda move: move.is_invoice(include_receipts=True)):
            if (
                invoice.quick_edit_mode
                and invoice.quick_edit_total_amount
                and invoice.currency_id.compare_amounts(invoice.quick_edit_total_amount, invoice.amount_total) != 0
            ):
                raise UserError(_(
                    "The current total is %s but the expected total is %s. In order to post the invoice/bill, "
                    "you can adjust its lines or the expected Total (tax inc.).",
                    formatLang(self.env, invoice.amount_total, currency_obj=invoice.currency_id),
                    formatLang(self.env, invoice.quick_edit_total_amount, currency_obj=invoice.currency_id),
                ))
            if invoice.partner_bank_id and not invoice.partner_bank_id.active:
                raise UserError(_(
                    "The recipient bank account linked to this invoice is archived.\n"
                    "So you cannot confirm the invoice."
                ))
            if float_compare(invoice.amount_total, 0.0, precision_rounding=invoice.currency_id.rounding) < 0:
                raise UserError(_(
                    "You cannot validate an invoice with a negative total amount. "
                    "You should create a credit note instead. "
                    "Use the action menu to transform it into a credit note or refund."
                ))

            if not invoice.partner_id:
                if invoice.is_sale_document():
                    raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
                elif invoice.is_purchase_document():
                    raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

            # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly.
            if not invoice.invoice_date:
                if invoice.is_sale_document(include_receipts=True):
                    invoice.invoice_date = fields.Date.context_today(self)
                elif invoice.is_purchase_document(include_receipts=True):
                    raise UserError(_("The Bill/Refund date is required to validate this document."))

        for move in self:
            if move.state in ['posted', 'cancel']:
                raise UserError(_('The entry %s (id %s) must be in draft.', move.name, move.id))
            if not move.line_ids.filtered(lambda line: line.display_type not in ('line_section', 'line_note')):
                raise UserError(_('You need to add a line before posting.'))
            if not soft and move.auto_post != 'no' and move.date > fields.Date.context_today(self):
                date_msg = move.date.strftime(get_lang(self.env).date_format)
                raise UserError(_("This move is configured to be auto-posted on %s", date_msg))
            if not move.journal_id.active:
                raise UserError(_(
                    "You cannot post an entry in an archived journal (%(journal)s)",
                    journal=move.journal_id.display_name,
                ))
            if move.display_inactive_currency_warning:
                raise UserError(_(
                    "You cannot validate a document with an inactive currency: %s",
                    move.currency_id.name
                ))

            if move.line_ids.account_id.filtered(lambda account: account.deprecated) and not self._context.get('skip_account_deprecation_check'):
                raise UserError(_("A line of this move is using a deprecated account, you cannot post it."))

        if soft:
            # future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
            # for move in future_moves:
            #     if move.auto_post == 'no':
            #         move.auto_post = 'at_date'
            #     msg = _('This move will be posted at the accounting date: %(date)s', date=format_date(self.env, move.date))
            #     move.message_post(body=msg)
            to_post = self
        else:
            to_post = self

        for move in to_post:
            affects_tax_report = move._affect_tax_report()
            lock_dates = move._get_violated_lock_dates(move.date, affects_tax_report)
            if lock_dates:
                move.date = move._get_accounting_date(move.invoice_date or move.date, affects_tax_report)

        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        to_post.line_ids._create_analytic_lines()

        # Trigger copying for recurring invoices
        to_post.filtered(lambda m: m.auto_post not in ('no', 'at_date'))._copy_recurring_entries()

        for invoice in to_post:
            # Fix inconsistencies that may occure if the OCR has been editing the invoice at the same time of a user. We force the
            # partner on the lines to be the same as the one on the move, because that's the only one the user can see/edit.
            wrong_lines = invoice.is_invoice() and invoice.line_ids.filtered(lambda aml:
                aml.partner_id != invoice.commercial_partner_id
                and aml.display_type not in ('line_note', 'line_section')
            )
            if wrong_lines:
                wrong_lines.write({'partner_id': invoice.commercial_partner_id.id})

        # reconcile if state is in draft and move has reversal_entry_id set
        draft_reverse_moves = to_post.filtered(lambda move: move.reversed_entry_id and move.reversed_entry_id.state == 'posted')

        to_post.write({
            'state': 'posted',
            'posted_before': True,
        })

        draft_reverse_moves.reversed_entry_id._reconcile_reversed_moves(draft_reverse_moves, self._context.get('move_reverse_cancel', False))
        to_post.line_ids._reconcile_marked()

        for invoice in to_post:
            invoice.message_subscribe([
                p.id
                for p in [invoice.partner_id]
                if p not in invoice.sudo().message_partner_ids
            ])

            if (
                invoice.is_sale_document()
                and invoice.journal_id.sale_activity_type_id
                and (invoice.journal_id.sale_activity_user_id or invoice.invoice_user_id).id not in (self.env.ref('base.user_root').id, False)
            ):
                invoice.activity_schedule(
                    date_deadline=min((date for date in invoice.line_ids.mapped('date_maturity') if date), default=invoice.date),
                    activity_type_id=invoice.journal_id.sale_activity_type_id.id,
                    summary=invoice.journal_id.sale_activity_note,
                    user_id=invoice.journal_id.sale_activity_user_id.id or invoice.invoice_user_id.id,
                )

        customer_count, supplier_count = defaultdict(int), defaultdict(int)
        for invoice in to_post:
            if invoice.is_sale_document():
                customer_count[invoice.partner_id] += 1
            elif invoice.is_purchase_document():
                supplier_count[invoice.partner_id] += 1
            elif invoice.move_type == 'entry':
                sale_amls = invoice.line_ids.filtered(lambda line: line.partner_id and line.account_id.account_type == 'asset_receivable')
                for partner in sale_amls.mapped('partner_id'):
                    customer_count[partner] += 1
                purchase_amls = invoice.line_ids.filtered(lambda line: line.partner_id and line.account_id.account_type == 'liability_payable')
                for partner in purchase_amls.mapped('partner_id'):
                    supplier_count[partner] += 1
        for partner, count in customer_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('customer_rank', count)
        for partner, count in supplier_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('supplier_rank', count)

        # Trigger action for paid invoices if amount is zero
        to_post.filtered(
            lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
        )._invoice_paid_hook()

        return to_post

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def standard_price_correction(self, product_ids=None):
        if not product_ids:
            product_ids = self.env['product.product'].search([]).ids
        stock_valuation = self.env['stock.valuation.layer'].search([
            ('product_id', '=', product_ids),
            ('stock_move_id', '=', False),
            ('quantity', '=', 0)
        ])
        if stock_valuation:
            stock_valuation.write({
                'value': 0,
                'unit_cost': 0,
            })
        line_ids = self.env['purchase.order.line'].search([('product_id', 'in', product_ids)])
        move_lines = self.env['stock.move'].search([('purchase_line_id', 'in', line_ids.ids)])
        # line_ids = self.mapped('picking_id').id
        # move_lines = self.env['stock.move'].search([('picking_id','=',line_ids)])
        for line in move_lines:
            line.product_price_update_before_done(
                forced_qty=sum(
                    [valued_move_line.product_uom_id._compute_quantity(valued_move_line.quantity, line.product_id.uom_id)
                     for valued_move_line in line._get_in_move_lines()]) * -1,
                is_new=True,
            )
            self.env['account.move'].update_stock_move_line(line)
        if move_lines:
            self.env.cr.commit()
            for line in self.env['stock.move'].search([
                ('product_id', 'in', move_lines.mapped('product_id').ids),
                ('purchase_line_id', '=', False),
                ('date', '>=', move_lines[0].date),
                ('id', 'not in', move_lines.ids)
            ]):
                self.env['account.move'].update_stock_move_line(line)
                self.env.cr.commit()
            for product in move_lines.mapped('product_id'):
                line = move_lines.filtered(lambda x: x.product_id.id == product.id).sorted(lambda x: x.date)[-1]
                line.product_price_update_before_done(
                    forced_qty=sum(
                        [valued_move_line.product_uom_id._compute_quantity(valued_move_line.quantity, line.product_id.uom_id)
                         for valued_move_line in line._get_in_move_lines()]) * -1,
                    is_new=True,
                )

# product_ids = 167418
# purchase_id = 252
# line_ids = self.env['purchase.order.line'].search([('product_id', '=', product_ids), ('order_id', '=', purchase_id)])
# line = self.env['stock.move'].search([('purchase_line_id', 'in', line_ids.ids)])
# line[1]._get_avg_sql_price_unit()
# valuation = self.env['stock.valuation.layer'].search([('stock_move_id', '=', line.id)])
# if valuation:
#     unit_price = line._get_avg_sql_price_unit()
#     valued_move_lines = line._get_in_move_lines()
#     valued_quantity = 0
#     for valued_move_line in valued_move_lines:
#         valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, line.product_id.uom_id)
#     for i in valuation:
#         i.write({
#             'value': line.company_id.currency_id.round(unit_price * i.quantity),
#             'unit_cost': unit_price,
#         })
#     for move in self.env['account.move'].search([('stock_move_id', '=', line.id)]):
#         move.button_draft()
#         move.line_ids.unlink()
#         vals = line._account_entry_move(valuation.quantity, valuation.description, valuation.id, valuation.value)[0]
#         vals['date'] = move.date
#         move.write(vals)
#         move._post()
#         if valuation.company_id.anglo_saxon_accounting:
#             valuation.stock_move_id._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=valuation.product_id)
