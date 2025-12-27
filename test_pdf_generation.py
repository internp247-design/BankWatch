#!/usr/bin/env python
"""Test PDF generation to diagnose issues"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, lightgrey
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO

def test_basic_pdf():
    """Test basic PDF generation"""
    print("Testing basic PDF generation...")
    
    try:
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Simple test
        elements.append(Paragraph("TEST PDF", styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(elements)
        
        # Check buffer
        pdf_data = pdf_buffer.getvalue()
        print(f"✓ PDF generated successfully. Size: {len(pdf_data)} bytes")
        print(f"✓ First 20 bytes: {pdf_data[:20]}")
        
        # Save to file for testing
        with open('test_output.pdf', 'wb') as f:
            f.write(pdf_data)
        print("✓ Test PDF saved to test_output.pdf")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_table():
    """Test PDF with table similar to the export"""
    print("\nTesting PDF with table...")
    
    try:
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Add title
        elements.append(Paragraph("TEST TABLE PDF", styles['Heading1']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Create test data
        col_widths = [0.85*inch, 0.85*inch, 3.5*inch, 0.8*inch, 1.1*inch, 1.1*inch]
        
        # Description style with wrapping
        desc_style = ParagraphStyle(
            'DescriptionStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT,
            leading=10,
            wordWrap='CJK'
        )
        
        table_data = [
            ['Date', 'Account', 'Description', 'Amount', 'Rule', 'Category']
        ]
        
        # Add test rows
        for i in range(5):
            desc = Paragraph(f"Test transaction {i} with a longer description that should wrap properly", desc_style)
            table_data.append([
                f'2025-01-{i+1:02d}',
                f'Account {i}',
                desc,
                f'₹{100*(i+1):,.2f}',
                f'Rule {i}',
                f'Category {i}'
            ])
        
        # Create table with FIXED hex colors
        table = Table(table_data, colWidths=col_widths, splitByRow=True)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#0D47A1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, lightgrey),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # Check buffer
        pdf_data = pdf_buffer.getvalue()
        print(f"✓ PDF with table generated successfully. Size: {len(pdf_data)} bytes")
        
        # Save to file for testing
        with open('test_output_table.pdf', 'wb') as f:
            f.write(pdf_data)
        print("✓ Test PDF with table saved to test_output_table.pdf")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success1 = test_basic_pdf()
    success2 = test_with_table()
    
    if success1 and success2:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed!")
