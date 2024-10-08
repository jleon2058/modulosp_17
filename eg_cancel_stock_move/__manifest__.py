{
    'name': 'Cancel Stock Moves',
    'version': '15.0',
    'category': 'Warehouse',
    'summery': 'Simple to refuse or cancel stock moves.',
    'author': 'INKERP',
    'website': "https://www.INKERP.com",
    'depends': ['stock','account'],
    
    'data': [
            'views/stock_move_view.xml',
            'views/account_move.xml'
    ],
    
    'images': ['static/description/banner.png'],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}
