from flask import Blueprint, send_file, request
from app.auth_utils import jwt_required_with_user, get_current_organisation_id, require_role
from app.services.reporting_service import ReportingService
from datetime import datetime

reports_bp = Blueprint("reports", __name__)

def parse_dates():
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    date_from = None
    date_to = None
    if date_from_str:
        try:
            date_from = datetime.fromisoformat(date_from_str)
        except ValueError:
            pass
    if date_to_str:
        try:
            date_to = datetime.fromisoformat(date_to_str)
        except ValueError:
            pass
    return date_from, date_to

@reports_bp.route("/asset-register", methods=["GET"])
@jwt_required_with_user
@require_role("admin", "auditor")
def export_asset_register():
    org_id = get_current_organisation_id()
    fmt = request.args.get("format", "pdf")
    date_from, date_to = parse_dates()
    
    file_buffer = ReportingService.get_asset_register(org_id, format=fmt, date_from=date_from, date_to=date_to)
    
    mimetype = "application/pdf" if fmt == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ext = "pdf" if fmt == "pdf" else "xlsx"
    
    return send_file(
        file_buffer,
        mimetype=mimetype,
        as_attachment=True,
        download_name=f"asset_register.{ext}"
    )

@reports_bp.route("/maintenance", methods=["GET"])
@jwt_required_with_user
@require_role("admin", "store_manager")
def export_maintenance_report():
    org_id = get_current_organisation_id()
    date_from, date_to = parse_dates()
    file_buffer = ReportingService.get_condition_report(org_id, condition='needs_repair', date_from=date_from, date_to=date_to)
    return send_file(file_buffer, mimetype="application/pdf", as_attachment=True, download_name="maintenance_report.pdf")

@reports_bp.route("/disposal", methods=["GET"])
@jwt_required_with_user
@require_role("admin", "store_manager")
def export_disposal_report():
    org_id = get_current_organisation_id()
    date_from, date_to = parse_dates()
    file_buffer = ReportingService.get_condition_report(org_id, condition='condemned', date_from=date_from, date_to=date_to)
    return send_file(file_buffer, mimetype="application/pdf", as_attachment=True, download_name="disposal_report.pdf")

@reports_bp.route("/audit-trail", methods=["GET"])
@jwt_required_with_user
@require_role("admin", "auditor")
def export_audit_report():
    org_id = get_current_organisation_id()
    date_from, date_to = parse_dates()
    file_buffer = ReportingService.get_audit_trail(org_id, date_from=date_from, date_to=date_to)
    return send_file(file_buffer, mimetype="application/pdf", as_attachment=True, download_name="audit_trail.pdf")

@reports_bp.route("/department-summary", methods=["GET"])
@jwt_required_with_user
@require_role("admin")
def export_dept_summary():
    org_id = get_current_organisation_id()
    date_from, date_to = parse_dates()
    file_buffer = ReportingService.get_department_summary(org_id, date_from=date_from, date_to=date_to)
    return send_file(
        file_buffer, 
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        as_attachment=True, 
        download_name="departmental_summary.xlsx"
    )
