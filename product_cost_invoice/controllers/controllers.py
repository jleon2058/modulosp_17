# -*- coding: utf-8 -*-
# from odoo import http


# class ProductCostInvoice(http.Controller):
#     @http.route('/product_cost_invoice/product_cost_invoice', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_cost_invoice/product_cost_invoice/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_cost_invoice.listing', {
#             'root': '/product_cost_invoice/product_cost_invoice',
#             'objects': http.request.env['product_cost_invoice.product_cost_invoice'].search([]),
#         })

#     @http.route('/product_cost_invoice/product_cost_invoice/objects/<model("product_cost_invoice.product_cost_invoice"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_cost_invoice.object', {
#             'object': obj
#         })
