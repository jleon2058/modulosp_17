{
    'name': """
        Target Entries for Invoices and Accounting Entries| 
        Asientos de Destino para Facturas y Asientos Contables
    """,

    'summary': """
        Generates of target entries or entries by nature automatically. |
        Genera asientos de destino o asientos por naturaleza automáticamente.
    """,

    'description': """
        Set up destination accounts from the chart of accounts and generate destination entries automatically. |
        Configura cuentas de destino desde el plan contable y genera asientos de destino automáticamente.
    """,

	'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'LGPL-3',

    'category': 'Accounting',
    'version': '15.0',

    'price': 49.99,
    'currency': 'EUR',

    'depends': [
        'base',
        'account',
    ],

    'data': [
        'views/account_move_views.xml',
        'views/account_analytic_account_views.xml',
        'views/account_account_views.xml',
    ],

    'images': ['static/description/banner.gif'],

    'application': True,
    'installable': True,
    'auto_install': False,
}
