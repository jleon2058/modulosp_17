import xlsxwriter
import calendar
import pytz
import base64
from datetime import datetime,date,timedelta
from pytz import timezone
from io import BytesIO
from odoo import models,fields,api, _,tools
from .formats import Cellformato
from .sql_queries import SQLQueries
from dateutil import relativedelta
import locale
import logging
logger = logging.getLogger(__name__)

class DateReportWizard(models.TransientModel,Cellformato,SQLQueries):
    _name = 'ind.kardexval.general'
    _description = 'Reporte de Kardex Valorado General'

    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    file_data = fields.Binary('File', readonly=True)
    # product_id = fields.Many2one('product.template',string="Producto")
    product_id = fields.Many2one('product.product',string="Producto", context="{'no_create_edit': True}")
    categoria_producto_id = fields.Many2one('product.category',string="Categoria", context="{'no_create_edit': True}")
    company_id = fields.Many2one('res.company',string='Compañia',default=lambda self: self.env.company,readonly=True,invisible=True)
    check_dolares = fields.Boolean(string='Reporte en Dolares')

# 1. DEFINICION DE FORMATOS

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('America/Lima'))
    
    def get_first_day_mounth(self,input_date):
        year = input_date.year
        month = input_date.month

        first_day = datetime(year, month, 1).date()

        return first_day
    
    def get_last_day_mounth(self,input_date):
        year = input_date.year
        month = input_date.month

        last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date()

        return last_day
    
    # def obtener_fecha_formateada(self):
        
    #     # locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
    #     for record in self:
    #         fecha_obj=record.date_from
    #         month_name = fecha_obj.strftime("%B")
    #         anio = fecha_obj.year
    #         fecha_formateada = f"{month_name} {anio}"
    #         print(fecha_formateada)
    

# 2. FUNCION QUE GENERA EL REPORTE DE EXCEL

    def generate_excel_report(self):

        data=self.read()[0]
        date_from = data['date_from']
        date_to = data['date_to']
        product_id = data['product_id']
        # locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
        # Crear un archivo Excel en memoria
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        cell_format, workbook = self.cell_format(workbook)

        first_day_mounth = self.get_first_day_mounth(date_from)
        last_day_mounth = self.get_last_day_mounth(date_to)

# 3. EXTRACCIÓN DE DATOS MEDIANTE CONSULTA SQL

    # 4.1. OBTENCIÓN DE CATEGORIAS Y PRODUCTOS ASOCIADOS POR CATEGORIA

        if self.product_id:
            categorias_obtenidos_padre = self.product_id.categ_id
            logger.warning("-------Categorias Padres-if--------")
            logger.warning(categorias_obtenidos_padre)
        
        elif self.categoria_producto_id:
            categorias_obtenidos_padre = self.categoria_producto_id
            logger.warning("-------Categorias Padres-elif--------")
            logger.warning(categorias_obtenidos_padre)

        else:
            #categorias_obtenidos=self.env['product.category'].search([])
            categorias_obtenidos_padre = self.env['product.category'].search([('parent_id','=',False)])
            logger.warning("-------Categorias Padres-else--------")
            logger.warning(categorias_obtenidos_padre)

        for category_padre in categorias_obtenidos_padre:
        #for category_padre in categorias_hija
            
            #categorias_obtenidos = self.env['product.category'].search([('parent_id','=',category_padre)]).ids
            if self.product_id:
                categorias_hija = self.product_id.categ_id
            # elif self.categoria_producto_id:
            #     categorias_hija = self.env['product.category'].search([('parent_id','=',category_padre.id)])
            else:
                #categorias_hija = category_padre
                categorias_hija = self.env['product.category'].search([('parent_id','=',category_padre.id)])

            logger.warning("-------Categorias hijas---------")
            logger.warning(categorias_hija)
            
            worksheet = workbook.add_worksheet(category_padre.name)
            now = datetime.now() - timedelta(hours=5)

            worksheet.write('A3',_('PERIODO:'),cell_format['datos'])
            worksheet.write('A4',_('RUC:'),cell_format['datos'])
            worksheet.write('A5',_('APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL'),cell_format['datos'])
            worksheet.write('A6',_('ESTABLECIMIENTO (1)'),cell_format['datos'])
            worksheet.write('A7',_('CÓDIGO DE EXISTENCIA'),cell_format['datos'])
            worksheet.write('A8',_('TIPO (TABLA 5):'),cell_format['datos'])
            worksheet.write('A9',_('DESCRIPCIÓN'),cell_format['datos'])
            worksheet.write('A10',_('CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6):'),cell_format['datos'])
            worksheet.write('A11',_('MÉTODO DE VALUACIÓN:'),cell_format['datos'])
            worksheet.write('A12',_('MONEDA:'),cell_format['datos'])

            if ((self.date_from.strftime('%Y-%m-%d') == first_day_mounth.strftime('%Y-%m-%d')) and (self.date_to.strftime('%Y-%m-%d') == last_day_mounth.strftime('%Y-%m-%d'))):
                # locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
                # worksheet.write('E3',f'{self.date_from.strftime('%B')} {self.date_from.year}')
                worksheet.write('E3',f"{self.date_from.strftime('%B')} {self.date_from.year}")
            else:
                worksheet.write('E3',f'{date_from}  -  {date_to}')    
                # worksheet.write('E3',first_day_of_month_from.strftime('%Y-%m-%d'))
                worksheet.write('E4',self.company_id.vat)
                worksheet.write('E5',self.company_id.name)
                worksheet.write('E6',self.company_id.street)

            name_categoria = category_padre.name
            if name_categoria:
                partes_categoria = name_categoria.split('-')
            else:
                partes_categoria = ["",""]
                codigo_categoria = partes_categoria[0]
                nombre_categoria = '-'.join(partes_categoria[1:])
                worksheet.write('E7',codigo_categoria)
                worksheet.write('E8','SUMINISTROS DIVERSOS')
                worksheet.write('E9',nombre_categoria)
                worksheet.write('E11','PROMEDIO')
                worksheet.write('E12','DOLARES' if self.check_dolares==True else 'SOLES')

            column1 = [
                _('FECHA'),
                _('TIPO (TABLA 10)'),
                _('SERIE'),
                _('NUMERO')]
            
            column2 = [
                _('CANTIDAD'),
                _('COSTO UNITARIO'),
                _('COSTO TOTAL'),
                _('CANTIDAD'),
                _('COSTO UNITARIO'),
                _('COSTO TOTAL'),
                _('CANTIDAD'),
                _('COSTO UNITARIO'),
                _('COSTO TOTAL')
            ]

            column_length = len(column1)+len(column2)+2

            if not column_length:
                return False
            
            no = 1
            column = 0  

            worksheet.merge_range('E14:E16',_('TIPO DE OPERACION (TABLA 12)'),cell_format['cabecera'])
            worksheet.merge_range('F14:F16',_('UBICACION'),cell_format['cabecera'])
            worksheet.merge_range('A14:D14',_('DOCUMENTO DE TRASLADO , COMPROBANTE DE PAGO'),cell_format['cabecera'])
            worksheet.merge_range('A15:D15',_('DOCUMENTO INTERNO O SIMILAR'),cell_format['cabecera'])
            worksheet.write('A1',_('FORMATO 13.1: "REGISTRO DE INVENTARIO PERMANENTE VALORIZADO - DETALLE DEL INVENTARIO VALORIZADO"') ,cell_format['title'])
            worksheet.merge_range('G14:I15',_('ENTRADAS'),cell_format['total'])
            worksheet.merge_range('J14:L15',_('SALIDAS'),cell_format['total'])
            worksheet.merge_range('M14:O15',_('SALDO FINAL'),cell_format['total'])

            for col in column1:
                worksheet.write(15,column,col,cell_format['header'])
                column+=1
            
            no = 1
            column = 0
            
            for col in column2:
                worksheet.write(15,column+6,col,cell_format['header'])
                column+=1
            
            worksheet.set_column('A:A', 20)
            worksheet.set_column('B:D', 10)
            worksheet.set_column('E:E', 25)
            worksheet.set_column('G:O', 16)

            row=17
            
            contador_registros = 0
            
            for category in categorias_hija:
                
                if self.product_id:
                    product_obtenidos = self.product_id
                
                else:
                    product_obtenidos = self.env['product.product'].search([('categ_id','=',category.id)])
                logger.warning("-------product obtenidos---------")
                logger.warning(product_obtenidos)

                if product_obtenidos:
            
# 4.2. CREACION DE LOS DATOS DE LA CABECERA PRINCIPAL POR CADA HOJA DEL REPORTE

            # locale.setlocale(locale.LC_TIME, 'es_ES.utf8')

            # worksheet.write('E3',f'{date_from}  -  {date_to}')
                
# 4.3. OBTENCIÓN DEL SALDO INICIAL

# 4.3.1. Calculo de las Cantidad del Saldo Inicial

                    results = []
                    #contador_registros = 0
                    lista_unidades = []

                if self.product_id:
                    producto=self.product_id
                    product_obtenidos=producto

                for producto in product_obtenidos:
                    logger.warning("-------row-1-------")
                    logger.warning(row)
                    logger.warning("-------product-------")
                    logger.warning(producto)  
                    if producto.uom_id.codigo_sunat not in lista_unidades:
                        lista_unidades.append(producto.uom_id.codigo_sunat)

                    cant_saldo_inicial=0
                    monto_saldo_inicial=0
 
                # Query en otro archivo

                    sql_cant_inicial=self.get_cant_inicial_query()

                    if producto:
                        self.env.cr.execute(sql_cant_inicial,(producto.id,self.date_from,self.company_id.id))
                        resultado_saldoinicial = self.env.cr.fetchone()

                    logger.warning("----resultado_saldoinicial-----")
                    logger.warning(resultado_saldoinicial) 
# 4.3.2. Calculo deL monto del Saldo Inicial

            # Query en otro archivo

                    if self.check_dolares:
                        sql_monto_inicial=self.get_monto_inicial_query_dolares()
                    else:
                        sql_monto_inicial=self.get_monto_inicial_query()

                    if producto:
                        self.env.cr.execute(sql_monto_inicial,(producto.id,self.date_from,self.company_id.id))
                        resultado_montoinicial = self.env.cr.fetchone()
                    
                    logger.warning("----resultado_monto_inicial-----")
                    logger.warning(resultado_montoinicial) 

            # Query en otro archivo
                    if self.check_dolares:
                        sql_monto_inicial_ajuste=self.get_ajuste_monto_inicial_query_dolares()
                    else:
                        sql_monto_inicial_ajuste=self.get_ajuste_monto_inicial_query()

                    if producto:
                        self.env.cr.execute(sql_monto_inicial_ajuste,(producto.id,self.date_from,self.company_id.id))
                        resultado_ajuste_montoinicial = self.env.cr.fetchone()
# 4.3.2. Calculo del Promedio del Saldo Inicial
        
                    cant_saldo_inicial = resultado_saldoinicial[0]
                    monto_saldo_inicial = resultado_montoinicial[0]+resultado_ajuste_montoinicial[0]

                    if cant_saldo_inicial > 0:
                        costo_promedio_inicial = round(monto_saldo_inicial / cant_saldo_inicial,6)
                    else:
                        costo_promedio_inicial = 0

# 3.5. OBTENCIÓN DE LOS REGISTROS DENTRO DEL RANGO DE FECHAS SELECCIONADAS

# 3.5.1. Extracción de datos dentro del rango seleccionado

                    data_lista = []
                    data_diccionario = {}
                    data_diccionario_ordenado = {}

                    diccionario_ajustes ={}
                    diccionario_ordenado_ajuste = {}
                    sql_ajuste_precio=None

                    sql = None
                    if producto:
                        #query para movimiento
                        sql=self.get_movimientos_query()
                        self.env.cr.execute(sql,(producto.id,self.date_from,self.date_to,self.company_id.id))
                    
                        results=self.env.cr.dictfetchall()

                        logger.warning("----resultss-----")
                        logger.warning(results) 

                        #query para ajuste de precio
                        sql_ajuste_precio=self.get_ajuste_precio_query()
                        self.env.cr.execute(sql_ajuste_precio,(producto.id,self.date_from,self.date_to,self.company_id.id))

                        resultado_ajuste_precio=self.env.cr.dictfetchall()

                        logger.warning("----resultss-ajuste----")
                        logger.warning(results) 

# 3.5.2. Almacenamiento de datos extraidos a un Diccionario

            # lista_clave_ordenada_location_id_guia = ['date','tipo_doc','serie_albaran','numero_albaran','tip_tabla12','location_name','product_uom_qty','precio_unit_asiento','monto_asiento','nombre_cc']
            # lista_clave_ordenada_location_id_factura = ['date','tipo_doc','serie_factura','num_factura','tip_tabla12','location_name','product_uom_qty','precio_unit_asiento','monto_asiento','nombre_cc']

            # lista_clave_ordenada_location_dest_id_guia = ['date','tipo_doc','serie_albaran','numero_albaran','tip_tabla12','location_dest_name','product_uom_qty','precio_unit_asiento','monto_asiento','nombre_cc']
            # lista_clave_ordenada_location_dest_id_factura = ['date','tipo_doc','serie_factura','num_factura','tip_tabla12','location_dest_name','product_uom_qty','precio_unit_asiento','monto_asiento','nombre_cc']

                    #if cant_saldo_inicial != 0 or monto_saldo_inicial != 0 or results:
                    if (cant_saldo_inicial > 0.0001 or cant_saldo_inicial < -0.0001) or \
                        (monto_saldo_inicial > 0.0001 or monto_saldo_inicial < -0.0001) or \
                        results:

                        logger.warning("----cant_saldo_inicial != 0----")
                        logger.warning(producto)

                        contador_registros+=1

                        lista_clave_ordenada_location_id = ['date','tipo_doc','serie_albaran','numero_albaran','tip_tabla12','location_name','product_uom_qty','precio_unit_asiento','monto_asiento','nombre_cc','id','tipo_cambio']
                        lista_clave_ordenada_location_dest_id = ['date','tipo_doc','serie_albaran','numero_albaran','tip_tabla12','location_dest_name','product_uom_qty','precio_unit_asiento','monto_asiento','nombre_cc','id','tipo_cambio']

                        for l in results:
                    # product_nombre=l.get('name')
                    # producto_nombre=product_nombre['es_PE']
                    
                    # guia=l.get('guia')
                    # if guia:
                    #     partes_guia=guia.split('-')
                    # else:
                    #     partes_guia=["",""]
                    # serie_guia=partes_guia[0]
                    # numero_guia='-'.join(partes_guia[1:])
                    # factura=l.get('factura')
                    # if factura:
                    #     partes_factura=factura.split('-')
                    # else:
                    #     partes_factura=["",""]
                    # serie_factura=partes_factura[0]
                    # num_factura='-'.join(partes_factura[1:])
                            productos_sm = self.env['stock.move'].browse(l.get('id')).mapped('product_id').ids
                            pick_id = self.env['stock.move'].browse(l.get('id')).mapped('picking_id').ids
                            factura_sm = self.env['account.move'].search([('invoice_line_ids.product_id','in',productos_sm),('transfer_ids','in',pick_id),('state','=','posted')]).mapped('name')
                            moneda_sm = self.env['account.move'].search([('invoice_line_ids.product_id','in',productos_sm),('transfer_ids','in',pick_id),('state','=','posted')]).mapped('currency_id').id

                    # if factura_sm.currency_id==2 and factura_sm:
                            if moneda_sm==2:
                                # fecha_asiento = factura_sm.invoice_date
                                fecha_asiento = self.env['account.move'].search([('invoice_line_ids.product_id','in',productos_sm),('transfer_ids','in',pick_id),('state','=','posted')]).invoice_date
                                tipo_cambio = self.env['res.currency.rate'].search([('name','=',fecha_asiento)]).mapped('inverse_company_rate')

                            else:
                                fecha_asiento = self.env['account.move'].search([('stock_move_id','=',l.get('id')),('state','=','posted')]).date
                                tipo_cambio = self.env['res.currency.rate'].search([('name','<=',fecha_asiento)]).mapped('inverse_company_rate')
                                
                            if fecha_asiento:
                                primer_tipo_cambio = tipo_cambio[0]
                                precio_unitario_sql_valor = l.get('precio_unit_asiento')
                                subtotal_sql_valor = l.get('monto_asiento')

                                if precio_unitario_sql_valor is not None and subtotal_sql_valor is not None and primer_tipo_cambio !=0:
                                    if self.check_dolares:
                                        precio_unitario_sql_valor = precio_unitario_sql_valor/primer_tipo_cambio
                                        subtotal_sql_valor = precio_unitario_sql_valor*(l.get('product_uom_qty'))
                            else:
                                primer_tipo_cambio = 0
                                precio_unitario_sql_valor = 0
                                subtotal_sql_valor = 0

                            data_diccionario = {
                                'id':l.get('id'),
                                'product_id':l.get('product_id'),
                                'product_uom_qty':l.get('product_uom_qty'),
                                'price_unit':l.get('price_unit'),
                                'location_id':l.get('location_id'),
                                'location_dest_id':l.get('location_dest_id'),
                                'default_code':l.get('default_code'),
                                'name':l.get('name'),
                                # 'name':producto_nombre,
                                'date':l.get('date'),
                                'location_name':l.get('location_name'),
                                'location_dest_name':l.get('location_dest_name'),
                                'reference':l.get('reference'),
                                'usage_dest_id':l.get('usage_dest_id'),
                                'usage_id':l.get('usage_id'),
                                # 'precio_unit_asiento':l.get('precio_unit_asiento'),
                                'precio_unit_asiento':precio_unitario_sql_valor,
                                # 'monto_asiento':l.get('monto_asiento'),
                                'monto_asiento':subtotal_sql_valor if subtotal_sql_valor is not None else 0,
                                'serie_albaran':'',
                                'numero_albaran':l.get('numero_albaran'),
                                'serie_factura':'1235',
                                'num_factura':'67895',
                                # 'serie_guia':l.get('serie_guia',' '),
                                # 'numero_guia':l.get('numero_guia',' '),
                                # 'serie_factura':l.get('serie_factura',' '),
                                # 'num_factura':l.get('num_factura',' '),
                                'tipo_doc':'00',
                                'tip_tabla12':'01',
                                'nombre_cc':l.get('nombre_cc'),
                                'tipo_cambio':primer_tipo_cambio
                            }
                            if data_diccionario['usage_dest_id'] == 'internal':

                                if data_diccionario['usage_id'] == 'supplier':
                                    data_diccionario['tip_tabla12'] = 'COMPRA'
                                elif data_diccionario['usage_id'] == 'production':
                                    data_diccionario['tip_tabla12'] = 'DEVOLUCIÓN RECIBIDA'
                                elif data_diccionario['usage_id'] == 'customer':
                                    data_diccionario['tip_tabla12'] = 'DEVOLUCIÓN RECIBIDA'
                                elif data_diccionario['usage_id'] == 'inventory':
                                    data_diccionario['tip_tabla12'] = 'INGRESO POR AJUSTE'

                                diccionario_ordenado = {clave: data_diccionario[clave] for clave in lista_clave_ordenada_location_id}

                            else:
                                if data_diccionario['usage_dest_id'] == 'supplier':
                                    data_diccionario['tip_tabla12'] = 'DEVOLUCIÓN ENTREGADA'
                                elif data_diccionario['usage_dest_id'] == 'production':
                                    data_diccionario['tip_tabla12'] = 'SALIDA A PRODUCCIÓN'
                                elif data_diccionario['usage_dest_id'] == 'customer':
                                    data_diccionario['tip_tabla12'] = 'VENTA'
                                elif data_diccionario['usage_dest_id'] == 'inventory':
                                    data_diccionario['tip_tabla12'] = 'CONSUMO POR AJUSTE'                    

                                # if data_diccionario['serie_factura'] and data_diccionario['num_factura']:
                                #     data_diccionario['tipo_doc'] = '01'
                                #     diccionario_ordenado = {clave: data_diccionario[clave] for clave in lista_clave_ordenada_location_dest_id_factura}
                                # else:
                                #     data_diccionario['tipo_doc'] = '00'
                                #     diccionario_ordenado = {clave: data_diccionario[clave] for clave in lista_clave_ordenada_location_dest_id_guia}
                                diccionario_ordenado = {clave: data_diccionario[clave] for clave in lista_clave_ordenada_location_dest_id}

                            data_lista.append(diccionario_ordenado)

                        for r in resultado_ajuste_precio:
                            # fecha_asiento_ajuste=r.get('date')
                            fecha_asiento_ajuste = self.env['account.move'].search([('id','=',r.get('move_id')),('state','=','posted')]).date
                            tipo_cambio_ajuste = self.env['res.currency.rate'].search([('name','<=',fecha_asiento_ajuste)]).mapped('inverse_company_rate')
                            primer_tipo_cambio_ajuste = tipo_cambio_ajuste[0]
                            ajuste_debit = r.get('debit')
                            ajuste_credit = r.get('credit')
                            if ajuste_debit is not None or ajuste_credit is not None and primer_tipo_cambio_ajuste !=0:
                                if self.check_dolares:
                                    ajuste_debit = ajuste_debit/primer_tipo_cambio_ajuste
                                    ajuste_credit = ajuste_credit/primer_tipo_cambio_ajuste
                            diccionario_ajustes={
                                'id':r.get('id'),
                                'date':r.get('create_date'),
                                'serie_albaran':'',
                                'location_name':'',
                                'location_dest_name':'',
                                'numero_albaran':r.get('move_name'),
                                'product_uom_qty':0,
                                'tipo_doc':'00',
                                'tip_tabla12':'AJUSTE',
                                # 'debit':r.get('debit'),
                                'debit':ajuste_debit,
                                # 'credit':r.get('credit'),
                                'credit':ajuste_credit,
                                'precio_unit_asiento':'',
                                'nombre_cc':'',
                                'tipo_cambio':primer_tipo_cambio_ajuste
                            }
                            if diccionario_ajustes.get('debit') is not None and diccionario_ajustes['debit']>0:
                                clave_nueva='monto_asiento'
                                diccionario_ajustes.update({clave_nueva:diccionario_ajustes.pop('debit')})
                                diccionario_ordenado_ajuste = {clave: diccionario_ajustes[clave] for clave in lista_clave_ordenada_location_id}
                            elif diccionario_ajustes.get('credit') is not None and diccionario_ajustes['credit']>0:
                                clave_nueva='monto_asiento'
                                diccionario_ajustes.update({clave_nueva:diccionario_ajustes.pop('credit')})
                                diccionario_ordenado_ajuste = {clave: diccionario_ajustes[clave] for clave in lista_clave_ordenada_location_dest_id}
                            
                            data_lista.append(diccionario_ordenado_ajuste)

                        data_lista_mov_ordenado = sorted(data_lista,key=lambda x: x['date'])
                # data_lista_mov_ordenado = sorted(data_lista, key=lambda x: datetime.combine(x['date'], datetime.min.time()) if isinstance(x['date'], date) else x['date'])

# 3.6. IMPRESION DE LOS DATOS OBTENIDOS EN EL REPORTE

# 3.6.1. Imnpresion de la Fila del Saldo Inicial
                
                        column_float_number = {}
                        cant_ingresa = {}
                        logger.warning("---------row-2-------")
                        logger.warning(row)
                        cant_saldo = cant_saldo_inicial
                        monto_saldo = monto_saldo_inicial

                        worksheet.write('A%s' % (row),  f"[{producto.default_code}] {producto.name}",
                                                cell_format['content_float'])
                        worksheet.write('D%s' % (row),producto.uom_id.name,
                                                cell_format['content_float'])
                        worksheet.write('E%s' % (row),'SALDO INICIAL',
                                                cell_format['content_float'])                        
                        worksheet.write('M%s' % (row), cant_saldo_inicial,
                                                cell_format['content_float'])
                        worksheet.write('N%s' % (row), costo_promedio_inicial,
                                                cell_format['decimal'])
                        worksheet.write('O%s' % (row), monto_saldo_inicial,
                                                cell_format['content_float'])                        

# 3.6.2. Impresión de los movimientos comprendidos dentro del rango de fechas

                        for data_diccionario in data_lista_mov_ordenado:

                            no += 1
                            column = 0
                            cont =0

                            for clave, value in data_diccionario.items():

                                if type(value) is int or type(value) is float:
                                    content_format = 'content_float'

                                    column_float_number[column] = column_float_number.get(
                                        column, 0) + value
                                else:
                                    content_format = 'content_float'

                                if isinstance(value, datetime):
                                    value = pytz.UTC.localize(value).astimezone(
                                        timezone(self.env.user.tz or 'UTC'))
                                    # value = value.strftime('%Y-%m-%d %H:%M:%S')
                                    value = value.strftime('%Y-%m-%d')
                                elif isinstance(value, date):
                                    value = value.strftime('%Y-%m-%d')

                                if cont==0:
                                    # if value is None:
                                    #     worksheet.write(row, column, 0,
                                    #                 cell_format[content_format])
                                    # else:
                                    if clave!='nombre_cc' and clave!='id' and clave!='tipo_cambio' and clave!='precio_unit_asiento':
                                        worksheet.write(row, column, value,cell_format[content_format])
                                    if clave == 'product_uom_qty':
                                        cant_saldo=cant_saldo+value
                                        worksheet.write(row,column+6,cant_saldo,cell_format[content_format])
                                        cant_ingresa[column] = cant_ingresa.get(column, 0) + value
                                    elif clave == 'precio_unit_asiento':
                                        worksheet.write(row, column, value,cell_format['decimal'])
                                    elif clave == 'monto_asiento':
                                        # if value is not None:
                                        monto_saldo = monto_saldo+value
                                        worksheet.write(row,column+6,monto_saldo,cell_format[content_format])
                                        cant_ingresa[column] = cant_ingresa.get(column, 0) + value
                                    elif clave == 'nombre_cc':
                                        worksheet.write(row,column+6,value,cell_format[content_format])
                                    elif clave == 'id':
                                        worksheet.write(row,column+6,value)
                                    elif clave == 'tipo_cambio':
                                        worksheet.write(row,column+6,value)

                                if column>=5 and cont>=1:
                                    # if value is None:
                                    #     worksheet.write(row, column+3, 0,
                                    #                 cell_format[content_format])
                                    # else:
                                    if clave != 'nombre_cc' and clave!='id' and clave!='tipo_cambio' and clave!='precio_unit_asiento':
                                        worksheet.write(row, column+3, value,cell_format[content_format])
                                    if clave == 'product_uom_qty':
                                        cant_saldo=cant_saldo-value
                                        worksheet.write(row,column+6,cant_saldo,cell_format[content_format])
                                        cant_ingresa[column+3] = cant_ingresa.get(column+3, 0) + value
                                    # elif clave == 'subtotal_sql':
                                    elif clave == 'precio_unit_asiento':
                                        worksheet.write(row, column+3, value,cell_format['decimal']) 
                                    elif clave == 'monto_asiento':
                                        # if value is not None:
                                        monto_saldo = monto_saldo-value
                                        worksheet.write(row,column+6,monto_saldo,cell_format[content_format])
                                        cant_ingresa[column+3] = cant_ingresa.get(column+3, 0) + value
                                    elif clave == 'nombre_cc':
                                        worksheet.write(row,column+6,value,cell_format[content_format])
                                    elif clave == 'id':
                                        worksheet.write(row,column+6,value)
                                    elif clave == 'tipo_cambio':
                                        worksheet.write(row,column+6,value)
                                    cont +=1
                                if clave=='location_dest_name':
                                    cont +=1
                                column += 1
                            
                            if cant_saldo>0:
                                    costo_promedio=round(monto_saldo/cant_saldo,6)
                                    worksheet.write(row, column+1,costo_promedio,cell_format['decimal'])
                            else:
                                worksheet.write(row, column+1,0)

# 3.5.3. Impresión de totales por productos en Cantidades y Montos        
                    
                            row += 1

                        for x in range(column_length):

                            # if x == 0:
                            #     worksheet.write('A%s' % (row + 1), _('Total'),
                            #                     cell_format['total'])
                            if x not in cant_ingresa:
                                if x==5:
                                    worksheet.write('E%s' % (row + 1), _('Total'),cell_format['total'])
                                elif x>5:
                                    worksheet.write(row, x, '', cell_format['total'])
                                elif x<5:
                                    # worksheet.write(row, x, '', cell_format['linealimite'])
                                    worksheet.write(row,x,f"[{producto.default_code}] {producto.name}", cell_format['linealimite'])
                            else:
                                worksheet.write(
                                    row, x, cant_ingresa[x], cell_format['total'])

                        row=row+3

                #row=row+3

                #div_categ=div_categ+5
            if contador_registros>0:
    
                cadena_unidades = ', '.join(map(str,lista_unidades))
                worksheet.write('E10',cadena_unidades)
            else:
                worksheet.hide()


# 5. CIERRE DEL LIBRO 

        workbook.close()

        result = base64.encodebytes(fp.getvalue()).decode('utf-8')
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        # filename = '%s %s' % (report_name, date_string)
        filename = 'Reporte'
        filename += '%2Exlsx'
        self.write({'file_data': result})

        url = "web/content/?model=" + self._name + "&id=" + str(
            self[:1].id) + "&field=file_data&download=true&filename=" + filename

        # output.seek(0)
        return {
            'name': _('Generic Excel Report'),
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }








