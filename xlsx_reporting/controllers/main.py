import json
import logging

from odoo.http import (
    content_disposition,
    request,
    route,
    serialize_exception as _serialize_exception,
)
from odoo.tools import html_escape
from odoo.tools.safe_eval import safe_eval, time
from werkzeug.urls import url_decode

from odoo.addons.web.controllers.report import ReportController

_logger = logging.getLogger(__name__)


class ReportControllerXlsx(ReportController):
    XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    @route()
    def report_routes(self, reportname='Unknown', docids=None, converter=None, **data):
        if converter != "xlsx":
            return super().report_routes(reportname, docids, converter, **data)
        report = request.env['ir.actions.report']
        context = dict(request.env.context)
        try:
            report = report._get_report_from_name(reportname)
            docids = [int(i) for i in docids.split(",")] if docids else []
            data.update(json.loads(data.pop("options"))) if data.get("options") else {}
            # context.update(json.loads(data.get("context", "{}")))
            if data.get("context"):
                data["context"] = json.loads(data["context"])
                context.update(data["context"])
            xlsx = report.with_context(**context)._render_xlsx(reportname, docids, data=data)[0]
            xlsx_headers = [("Content-Type", self.XLSX_CONTENT_TYPE), ("Content-Length", len(xlsx))]
            return request.make_response(xlsx, headers=xlsx_headers)
        except Exception as e:
            _logger.exception("Error generating XLSX report: %s", str(e))
            return request.make_response(
                "Error generating XLSX report: {}".format(html_escape(str(e))),
                headers=[("Content-Type", "text/plain")],
                status=500,
            )

    @route()
    def report_download(self, data, context=None, token=None):
        requestcontent = json.loads(data)
        url, report_type = requestcontent[0], requestcontent[1]
        try:
            if report_type != "xlsx":
                return super().report_download(data, context=context, token=token)
            reportname = url.split("/report/xlsx/")[1].split("?")[0]
            docids = None
            if "/" in reportname:
                reportname, docids = reportname.split("/")
            if docids:
                # Generic report:
                response = self.report_routes(
                    reportname, docids=docids, converter="xlsx", context=context
                )
            else:
                # Particular report:
                data = dict(
                    url_decode(url.split("?")[1]).items()
                )  # decoding the args represented in JSON
                if "context" in data:
                    context, data_context = json.loads(context or "{}"), json.loads(
                        data.pop("context")
                    )
                    context = json.dumps({**context, **data_context})
                response = self.report_routes(
                    reportname, converter="xlsx", context=context, **data
                )

            report = request.env["ir.actions.report"]._get_report_from_name(
                reportname
            )
            filename = "%s.%s" % (report.name, "xlsx")

            if docids:
                ids = [int(x) for x in docids.split(",")]
                obj = request.env[report.model].browse(ids)
                if report.print_report_name and not len(obj) > 1:
                    report_name = safe_eval(
                        report.print_report_name, {"object": obj, "time": time}
                    )
                    filename = "%s.%s" % (report_name, "xlsx")
            if not response.headers.get("Content-Disposition"):
                response.headers.add(
                    "Content-Disposition", content_disposition(filename)
                )
            return response
        except Exception as e:
            _logger.exception("Error while generating report %s", reportname)
            se = _serialize_exception(e)
            error = {"code": 200, "message": "Odoo Server Error", "data": se}
            return request.make_response(html_escape(json.dumps(error)))
