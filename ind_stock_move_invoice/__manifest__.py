{
    'name': "Indomin Invoice From Stock Picking",
    'summary': """In this module creating customer invoice,vendor bill, customer
    credit note and refund from stock picking""",
    'description': """In this module creating customer invoice,vendor bill, customer
    credit note and refund from stock picking""",
    'category': 'Stock',
    'author': 'Juan Carlos',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['stock', 'account','stock_move_invoice','purchase'],
    'data': [
        'views/stock_picking_inherited.xml',
        #'views/account_move.xml',
        #'views/purchase_order.xml',
        'views/account_move_line.xml',
        'views/stock_move.xml'
    ]
}