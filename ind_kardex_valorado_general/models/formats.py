from odoo import models
import xlsxwriter

class Cellformato(models.AbstractModel):
    _name = 'cell.format.helper'

    def cell_format(self,workbook):
        cell_format={}
        cell_format['title']=workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'font_size': 20,
            'font_name': 'Arial',
        })
        cell_format['header']=workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'center',
            # 'bg_color':'#0BBB20',
            'border': True,
            'font_name': 'Arial',
            'font_size': 10,
        })
        cell_format['content_float'] = workbook.add_format({
            'font_size': 11,
            'border': False,
            'num_format': '#,##0.00',
            'font_name': 'Arial',
        })
        cell_format['total'] = workbook.add_format({
            'bold': True,
            # 'bg_color':'#CDCD08',
            'num_format': '#,##0.00',
            'align': 'center',
            'valign': 'center',
            'border': True,
            'font_name': 'Arial'
        })
        cell_format['cabecera'] = workbook.add_format({
            'bold': True,
            # 'bg_color':'#CDCD08',
            'num_format': '#,##0.00',
            'align': 'center',
            'valign': 'center',
            'border': True,
            'font_name': 'Arial',
            'font_size':8
        })
        cell_format['datos'] = workbook.add_format({
            'bold': True,
            # 'bg_color':'#CDCD08',
            'num_format': '#,##0.00',
            'font_name': 'Arial',
            'font_size':8
        })
        cell_format['linealimite'] = workbook.add_format({
            'top': True
        })
        cell_format['decimal'] = workbook.add_format({
            'num_format':'0.000000'
        })

        return cell_format,workbook