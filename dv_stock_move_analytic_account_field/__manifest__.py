{
	'name': "Analytic Account on Stock Move and Stock Valuation Layer",
	'summary': "Allows to select an Analytic Account on Stock Move and Stock Valuation Layer",

	'author': 'Develogers',
	'website': 'https://develogers.com',
	'support': 'especialistas@develogers.com',
	'live_test_url': 'https://demo.develogers.com',
	'license': 'LGPL-3',

	'category': 'Extra Tools',
	'version': '15.0',

	'price': '49.99',
	'currency': 'EUR',

	'depends': [
		'base',
  		'account',
  		'stock',
		'stock_account',
	],

	'data': [
		'views/stock_valuation_layer_views.xml',
		'views/stock_picking_views.xml',
	],

	'images': ['static/description/banner.gif'],

	'application': True,
	'installable': True,
	'auto_install': False,

	'secuence': '1'
}
