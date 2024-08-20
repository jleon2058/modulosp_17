{
    'name':'Indomin Kardex Valorado General',
    'description':'Reporte de Kardex Valorado a nivel del almacen',
    'author':'Juan Carlos',
    'depends':[
        "base","stock","purchase_request","ind_unidadmedida","account","product"
    ],
    'data':[
        "security/res_group.xml",
        "models/kardexval_general.xml",
        "security/ir_model_access.xml",
        "views/stock_move.xml"
    ]
}