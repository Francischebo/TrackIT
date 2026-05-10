from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import io
from datetime import datetime

class ProfessionalPDFReport:
    """Helper to generate consistent professional institutional reports."""
    
    def __init__(self, title, org_name, landscape_mode=False):
        self.buffer = io.BytesIO()
        self.pagesize = landscape(A4) if landscape_mode else A4
        self.doc = SimpleDocTemplate(
            self.buffer, 
            pagesize=self.pagesize,
            rightMargin=20*mm, leftMargin=20*mm,
            topMargin=20*mm, bottomMargin=20*mm
        )
        self.title = title
        self.org_name = org_name
        self.styles = getSampleStyleSheet()
        self.elements = []
        
        # Custom Styles
        self.title_style = ParagraphStyle(
            'ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=10,
            textColor=colors.HexColor("#1e293b")
        )
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            fontSize=10,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=30
        )

    def _add_header(self):
        # Branding Header
        self.elements.append(Paragraph(f"NOVA LITE LIMITED", self.title_style))
        self.elements.append(Paragraph(f"INSTITUTION: {self.org_name.upper()}", self.header_style))
        self.elements.append(Paragraph(f"REPORT: {self.title}", self.styles['Heading2']))
        self.elements.append(Paragraph(f"GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
        self.elements.append(Spacer(1, 15*mm))

    def create_table(self, data, col_widths=None):
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")])
        ]))
        self.elements.append(t)

    def generate(self):
        self._add_header()
        self.doc.build(self.elements)
        self.buffer.seek(0)
        return self.buffer

class ProfessionalExcelReport:
    """Helper to generate high-expertise Excel spreadsheets."""
    
    @staticmethod
    def generate(title, headers, data):
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = title[:30]
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        center_align = Alignment(horizontal="center", vertical="center")
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        
        # Header
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = thin_border
            
        # Data
        for row_num, row_data in enumerate(data, 2):
            for col_num, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col_num, value=value)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="left", vertical="center")
                
                # Auto-width
                column_letter = openpyxl.utils.get_column_letter(col_num)
                current_width = ws.column_dimensions[column_letter].width or 10
                ws.column_dimensions[column_letter].width = max(current_width, len(str(value)) + 2)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer
