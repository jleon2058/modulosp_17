# select sm.id,sl.usage ,sl2.usage , sm.product_id , sm.monto_asiento , sm.date ,am.date, sm.asiento_id , rcr.name, rcr.rate as ratio , coalesce(sm.monto_asiento * rcr.rate) as monto_asiento_dolares, ultima_tasa.rate,coalesce (sm.monto_asiento*ultima_tasa.rate)  as monto_asiento_dolares_ultimo
# FROM stock_move sm
# left join product_product pp on (pp.id=sm.product_id)
# left join product_template pt on (pt.id=pp.product_tmpl_id)
# INNER JOIN stock_location sl ON sm.location_id = sl.id
# LEFT JOIN stock_location sl2 ON sm.location_dest_id = sl2.id
# left join account_move am on (sm.asiento_id=am.id)
# left join res_currency_rate rcr on (rcr.name=am.date)
# left join lateral(
# 	select rate
# 	from res_currency_rate
# 	where name<=sm.date and rate is not null 
# 	order by name desc
# 	limit 1
# ) ultima_tasa on true
# where sm.state = 'done'
# order by am.date

# QUERY AÑADIENDO EL TIPO DE CAMBIO EN LA FACTURA

# select sm.id,sl.usage ,sl2.usage , sm.product_id , sm.monto_asiento , sm.date ,am.date, sm.asiento_id , rcr.name, rcr.rate as ratio , coalesce(sm.monto_asiento * rcr.rate) as monto_asiento_dolares, ultima_tasa.rate as ratio_dia ,coalesce (sm.monto_asiento*ultima_tasa.rate)  as monto_asiento_dolares_ultimo, ultima_tasa_factura.ratio_factura , ultima_tasa_factura.nombre_factura,coalesce (sm.monto_asiento*ultima_tasa_factura.ratio_factura) as monto_dolares_factura , coalesce(sm.monto_asiento*ultima_tasa_factura.ratio_factura,sm.monto_asiento*ultima_tasa.rate) as monto_final_dolares
# FROM stock_move sm
# left join product_product pp on (pp.id=sm.product_id)
# left join product_template pt on (pt.id=pp.product_tmpl_id)
# INNER JOIN stock_location sl ON sm.location_id = sl.id
# LEFT JOIN stock_location sl2 ON sm.location_dest_id = sl2.id
# left join account_move am on (sm.asiento_id=am.id)
# left join res_currency_rate rcr on (rcr.name=am.date)
# left join lateral(
# 	select rate
# 	from res_currency_rate
# 	where name<=sm.date and rate is not null 
# 	order by name desc
# 	limit 1
# ) ultima_tasa on true
# LEFT JOIN LATERAL (
#     select
#         rcr_sub.rate as ratio_factura, am_sub.name as nombre_factura
#     FROM
#         account_move am_sub
#     LEFT JOIN
#         account_move_line aml ON (am_sub.id = aml.move_id)
#     LEFT JOIN
#         account_move_stock_picking_rel amsprel ON (am_sub.id = amsprel.account_move_id)
#     LEFT JOIN
#         stock_move sm_sub ON (sm_sub.product_id = aml.product_id)
#     LEFT JOIN
#         res_currency rc_sub ON (rc_sub.id = am_sub.currency_id)
#     LEFT JOIN
#         res_currency_rate rcr_sub ON (rcr_sub.name = am_sub.invoice_date)
#     WHERE
#         sm_sub.id = sm.id and
#         am_sub.state = 'posted'
#         and sm_sub.picking_id = amsprel.transfer_id
#         AND am_sub.currency_id = 2
# ) ultima_tasa_factura ON TRUE
# where sm.state = 'done'
# order by am.date

class SQLQueries:
    @staticmethod
    def get_cant_inicial_query():
        return """
            SELECT COALESCE(SUM(
                CASE
                    WHEN sl.usage != 'internal' AND sl.usage != 'view' AND sl2.usage = 'internal' THEN sm.product_uom_qty
                    WHEN sl.usage = 'internal' AND sl2.usage != 'internal' AND sl2.usage != 'view' THEN -sm.product_uom_qty
                    ELSE 0
                END
            ),0) AS resultante
            FROM stock_move sm
            LEFT JOIN product_product pp ON (pp.id=sm.product_id)
            LEFT JOIN product_template pt ON (pt.id=pp.product_tmpl_id)
            INNER JOIN stock_location sl ON sm.location_id = sl.id
            LEFT JOIN stock_location sl2 ON sm.location_dest_id = sl2.id
            WHERE pp.id = %s AND sm.state ='done' AND sm.date < %s AND sm.company_id = %s
        """

    @staticmethod
    def get_monto_inicial_query():
        return """
            SELECT COALESCE(SUM(
                CASE
                    WHEN sl.usage != 'internal' AND sl.usage != 'view' AND sl2.usage = 'internal' THEN sm.monto_asiento
                    WHEN sl.usage = 'internal' AND sl2.usage != 'internal' AND sl2.usage != 'view' THEN -sm.monto_asiento
                    ELSE 0
                END
            ),0) AS resultante
            FROM stock_move sm
            left join product_product pp on (pp.id=sm.product_id)
            left join product_template pt on (pt.id=pp.product_tmpl_id)
            INNER JOIN stock_location sl ON sm.location_id = sl.id
            LEFT JOIN stock_location sl2 ON sm.location_dest_id = sl2.id
            WHERE pp.id = %s and sm.state ='done' and sm.date < %s AND sm.company_id = %s
        """
        
    # @staticmethod
    # def get_monto_inicial_query_dolares():
    #     return """
    #         SELECT COALESCE(SUM(
    #             CASE
    #                 WHEN sl.usage != 'internal' AND sl2.usage = 'internal' THEN sm.monto_asiento*ultima_tasa.rate
    #                 WHEN sl.usage = 'internal' AND sl2.usage != 'internal' THEN -sm.monto_asiento*ultima_tasa.rate
    #                 ELSE 0
    #             END
    #         ),0) AS resultante_dolares
    #         FROM stock_move sm
    #         left join product_product pp on (pp.id=sm.product_id)
    #         left join product_template pt on (pt.id=pp.product_tmpl_id)
    #         INNER JOIN stock_location sl ON sm.location_id = sl.id
    #         LEFT JOIN stock_location sl2 ON sm.location_dest_id = sl2.id
    #         left join account_move am on (sm.asiento_id=am.id)
    #         left join res_currency_rate rcr on (rcr.name=am.date)
    #         left join lateral(
    #             select rate
    #             from res_currency_rate
    #             where name<=sm.date and rate is not null 
    #             order by name desc
    #             limit 1
    #         ) ultima_tasa on true
    #         where pt.id=%s and sm.state = 'done' and sm.date <= %s AND sm.company_id = %s
    #     """
    
    @staticmethod
    def get_monto_inicial_query_dolares():
        return"""
            SELECT COALESCE(SUM(
                CASE
                    WHEN sl.usage != 'internal' AND sl.usage != 'view' AND sl2.usage = 'internal' THEN coalesce(sm.monto_asiento*ultima_tasa_factura.ratio_factura,sm.monto_asiento*ultima_tasa.rate)
                    WHEN sl.usage = 'internal' AND sl2.usage != 'internal' AND sl2.usage != 'view' THEN -coalesce(sm.monto_asiento*ultima_tasa_factura.ratio_factura,sm.monto_asiento*ultima_tasa.rate)
                    ELSE 0
                END
            ),0) AS resultante_dolares
            FROM stock_move sm
            left join product_product pp on (pp.id=sm.product_id)
            left join product_template pt on (pt.id=pp.product_tmpl_id)
            INNER JOIN stock_location sl ON sm.location_id = sl.id
            LEFT JOIN stock_location sl2 ON sm.location_dest_id = sl2.id
            left join account_move am on (sm.asiento_id=am.id)
            left join res_currency_rate rcr on (rcr.name=am.date)
            left join lateral(
                select rate
                from res_currency_rate
                where name<=sm.date and rate is not null 
                order by name desc
                limit 1
            ) ultima_tasa on true
            LEFT JOIN LATERAL (
                select
                    rcr_sub.rate as ratio_factura, am_sub.name as nombre_factura
                FROM
                    account_move am_sub
                LEFT JOIN
                    account_move_line aml ON (am_sub.id = aml.move_id)
                LEFT JOIN
                    account_move_stock_picking_rel amsprel ON (am_sub.id = amsprel.account_move_id)
                LEFT JOIN
                    stock_move sm_sub ON (sm_sub.product_id = aml.product_id)
                LEFT JOIN
                    res_currency rc_sub ON (rc_sub.id = am_sub.currency_id)
                LEFT JOIN
                    res_currency_rate rcr_sub ON (rcr_sub.name = am_sub.invoice_date)
                WHERE
                    sm_sub.id = sm.id and
                    am_sub.state = 'posted'
                    and sm_sub.picking_id = amsprel.transfer_id
                    AND am_sub.currency_id = 2
            ) ultima_tasa_factura ON TRUE
            where pp.id=%s and sm.state = 'done' and sm.date <= %s AND sm.company_id = %s
        """


    @staticmethod
    def get_ajuste_monto_inicial_query():
        return"""
            select COALESCE(SUM(
                aml.debit-aml.credit
            ),0) as balance_ctas
            from account_move_line as aml
            left join account_move am on (am.id=aml.move_id)
            left join account_account aa on (aml.account_id = aa.id)
            left join account_journal aj on (aj.id = am.journal_id)
            where am.stock_move_id is null and aj.code = 'INV' and aa.account_type='asset_current' and aml.quantity > 0 
            and aml.product_id = %s and am.state ='posted' and am.date < %s AND aml.company_id = %s
        """
    
    @staticmethod
    def get_ajuste_monto_inicial_query_dolares():
        return"""
            select COALESCE(SUM(
                aml.debit*ultima_tasa.rate-aml.credit*ultima_tasa.rate
            ),0) as balance_ctas
            from account_move_line as aml
            left join account_move am on (am.id=aml.move_id)
            left join account_account aa on (aml.account_id = aa.id)
            left join account_journal aj on (aj.id = am.journal_id)
            left join res_currency_rate rcr on (rcr.name=am.date)
            left join lateral(
                select rate
                from res_currency_rate
                where name<=am.date and rate is not null 
                order by name desc
                limit 1
            ) ultima_tasa on true
            where am.stock_move_id is null and aj.code = 'INV' and aa.account_type='asset_current' and aml.quantity > 0 
            and aml.product_id = %s and am.state ='posted' and am.date < %s AND aml.company_id = %s
        """

    # @staticmethod
    # def get_movimientos_query():
    #     return"""
    #         SELECT sm.id , sm.product_id , sm.product_uom_qty , sm.price_unit , sm.location_id , sm.location_dest_id , pp.default_code , pt.name , 
    #                         sm.date ,sl2.name AS location_name , sl1.name AS location_dest_name , sm.reference , 
    #                         sl1.usage AS usage_dest_id ,sl2.usage AS usage_id, COALESCE(sm.precio_unit_asiento,0) AS precio_unit_asiento, COALESCE(sm.monto_asiento,0) AS monto_asiento, sm.reference AS numero_albaran ,aaa.code || ' ' || aaa.name AS nombre_cc
    #         FROM stock_move sm
    #         left join product_product pp on (pp.id=sm.product_id)
    #         left join product_template pt on (pt.id=pp.product_tmpl_id)
    #         left join stock_location sl1 on (sm.location_dest_id = sl1.id)
    #         left join stock_location sl2 on (sm.location_id = sl2.id)
    #         left join stock_picking sp on (sm.picking_id = sp.id)
    #         left join account_analytic_account aaa on (aaa.id = sm.account_analytic_id)
    #         WHERE pp.id = %s AND sm.state='done' AND sm.date >= %s AND (sm.date - INTERVAL '1 day') < %s AND sm.company_id = %s
    #             AND (
    #                 sm.location_dest_id IN (
    #                     SELECT id
    #                     FROM stock_location
    #                     WHERE usage != 'internal'
    #                 )
    #                 OR
    #                 sm.location_id IN (
    #                     SELECT id
    #                     FROM stock_location
    #                     WHERE usage != 'internal'
    #                 )
    #             )
    #     """

    @staticmethod
    def get_movimientos_query():
        return"""
            SELECT sm.id , sm.product_id , sm.product_uom_qty , sm.price_unit , sm.location_id , sm.location_dest_id , pp.default_code , pt.name , 
                            sm.date ,sl2.name AS location_name , sl1.name AS location_dest_name , sm.reference , 
                            sl1.usage AS usage_dest_id ,sl2.usage AS usage_id, COALESCE(sm.precio_unit_asiento,0) AS precio_unit_asiento, COALESCE(sm.monto_asiento,0) AS monto_asiento, sm.reference AS numero_albaran ,aaa.code || ' ' || aaa.name AS nombre_cc
            FROM stock_move sm
            left join product_product pp on (pp.id=sm.product_id)
            left join product_template pt on (pt.id=pp.product_tmpl_id)
            left join stock_location sl1 on (sm.location_dest_id = sl1.id)
            left join stock_location sl2 on (sm.location_id = sl2.id)
            left join stock_picking sp on (sm.picking_id = sp.id)
            left join account_analytic_account aaa on (aaa.id = sm.account_analytic_id)
            WHERE pp.id = %s AND sm.state='done' AND sm.date >= %s AND (sm.date - INTERVAL '1 day') < %s AND sm.company_id = %s
				AND (
			        (sl1.usage != 'internal' OR sl1.usage IS NULL)
			        OR
			        (sl2.usage != 'internal' OR sl2.usage IS NULL)
			    )
			    AND sl1.usage != 'view'  -- Nueva condición para excluir usage igual a 'view'
			    AND sl2.usage != 'view'
				AND NOT (
			        (sl1.usage = 'internal' AND sl2.usage = 'view')
			        OR
			        (sl1.usage = 'view' AND sl2.usage = 'internal')
			    )
        """
    
    @staticmethod
    def get_ajuste_precio_query():
        return"""
            SELECT aml.id, aml.move_name, am.create_date , COALESCE(aml.debit,0) AS debit , COALESCE(aml.credit,0) AS credit , am.id AS move_id
            FROM account_move_line aml
            left join account_move am on (am.id=aml.move_id)
            left join account_account aa on (aml.account_id = aa.id)
            left join account_journal aj on (aj.id = am.journal_id)
            where am.stock_move_id is null and aj.code = 'INV' and aa.account_type='asset_current' and aml.quantity > 0 and aml.product_id = %s 
            AND am.state ='posted' and am.date >= %s AND (am.date - INTERVAL '1 day') < %s AND aml.company_id = %s
        """