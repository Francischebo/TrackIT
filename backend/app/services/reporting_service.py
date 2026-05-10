from app.models.asset import Asset
from app.models.organization import Organization
from app.utils.reporting_engines import ProfessionalPDFReport, ProfessionalExcelReport
from app import db
from datetime import datetime

class ReportingService:
    """Service to handle specific institutional report types."""

    @staticmethod
    def get_asset_register(org_id, format='pdf', date_from=None, date_to=None):
        org = Organization.query.get(org_id)
        query = Asset.query.filter_by(organisation_id=org_id)
        
        if date_from:
            query = query.filter(Asset.created_at >= date_from)
        if date_to:
            query = query.filter(Asset.created_at <= date_to)
            
        assets = query.all()
        
        headers = ["Code", "Name", "Type", "Department", "Location", "Status", "Value"]
        data = []
        for a in assets:
            data.append([
                a.asset_code,
                a.name,
                a.type,
                a.department.name if a.department else "N/A",
                a.location or "N/A",
                a.status.replace('_', ' ').capitalize(),
                f"${a.current_value:,.2f}"
            ])

        if format == 'excel':
            return ProfessionalExcelReport.generate("Asset Register", headers, data)
        
        report = ProfessionalPDFReport("Full Asset Register", org.name, landscape_mode=True)
        report.create_table([headers] + data)
        return report.generate()

    @staticmethod
    def get_condition_report(org_id, condition='needs_repair', date_from=None, date_to=None):
        org = Organization.query.get(org_id)
        query = Asset.query.filter_by(organisation_id=org_id, condition=condition)
        
        if date_from:
            query = query.filter(Asset.created_at >= date_from)
        if date_to:
            query = query.filter(Asset.created_at <= date_to)
            
        assets = query.all()
        
        title = "Maintenance Report" if condition == 'needs_repair' else "Disposal Report"
        headers = ["Code", "Name", "Department", "Location", "Condition", "Current Value"]
        data = [[a.asset_code, a.name, a.department.name if a.department else "", a.location, a.condition, f"${a.current_value:,.2f}"] for a in assets]
        
        report = ProfessionalPDFReport(title, org.name)
        report.create_table([headers] + data)
        return report.generate()

    @staticmethod
    def get_audit_trail(org_id, date_from=None, date_to=None):
        from app.models.inventory import AuditLog
        org = Organization.query.get(org_id)
        query = AuditLog.query.filter_by(organisation_id=org_id)
        
        if date_from:
            query = query.filter(AuditLog.created_at >= date_from)
        if date_to:
            query = query.filter(AuditLog.created_at <= date_to)
            
        logs = query.order_by(AuditLog.created_at.desc()).limit(1000).all()
        
        headers = ["Timestamp", "Action", "Entity", "User", "Details"]
        data = [[l.created_at.strftime('%Y-%m-%d %H:%M'), l.action, f"{l.entity_type} #{l.entity_id}", f"User ID: {l.user_id}", str(l.details)[:50]] for l in logs]
        
        report = ProfessionalPDFReport("Institutional Audit Trail", org.name, landscape_mode=True)
        report.create_table([headers] + data)
        return report.generate()

    @staticmethod
    def get_department_summary(org_id, date_from=None, date_to=None):
        from app.models.organization import Department
        org = Organization.query.get(org_id)
        depts = Department.query.filter_by(organisation_id=org_id).all()
        
        headers = ["Department", "Asset Count", "Total Value", "Condition: Good", "Condition: Repair"]
        data = []
        for d in depts:
            query = Asset.query.filter_by(department_id=d.id)
            if date_from:
                query = query.filter(Asset.created_at >= date_from)
            if date_to:
                query = query.filter(Asset.created_at <= date_to)
            assets = query.all()
            
            data.append([
                d.name,
                len(assets),
                f"${sum(a.current_value for a in assets):,.2f}",
                len([a for a in assets if a.condition == 'good']),
                len([a for a in assets if a.condition == 'needs_repair'])
            ])
            
        return ProfessionalExcelReport.generate("Departmental Asset Summary", headers, data)
