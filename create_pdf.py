#!/usr/bin/env python3
"""
Convert MT5_INTEGRATION_GUIDE.md to PDF
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
import os

def create_pdf():
    # Read markdown
    with open('MT5_INTEGRATION_GUIDE.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # Create PDF
    pdf_file = 'MT5_INTEGRATION_GUIDE.pdf'
    doc = SimpleDocTemplate(pdf_file, pagesize=letter,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)

    # Define styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#004499'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4,
        alignment=0
    )

    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Normal'],
        fontSize=7.5,
        fontName='Courier',
        textColor=colors.HexColor('#333333'),
        spaceAfter=2,
        leftIndent=12
    )

    # Build story
    story = []

    # Add header
    story.append(Paragraph('TechnobizTrader', title_style))
    story.append(Paragraph('MetaTrader 5 Integration Guide', heading1_style))
    story.append(Paragraph('<b>Version:</b> 2.0 | <b>Date:</b> May 3, 2026 | <b>Status:</b> Production Ready', normal_style))
    story.append(Spacer(1, 0.2*inch))

    # Process lines
    lines = content.split('\n')
    page_count = 0

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Skip empty lines at beginning
        if not line_stripped:
            continue

        # Main titles
        if line_stripped.startswith('# ') and not line_stripped.startswith('## '):
            if page_count > 0:
                story.append(PageBreak())
            title = line_stripped.replace('# ', '')
            story.append(Paragraph(title, heading1_style))
            page_count += 1

        # Subtitles
        elif line_stripped.startswith('## '):
            title = line_stripped.replace('## ', '')
            story.append(Paragraph(title, heading2_style))

        # Skip code blocks (too complex for this simple converter)
        elif line_stripped.startswith('```'):
            story.append(Paragraph('<i>[Code Block - See markdown file for details]</i>', normal_style))
            # Skip until end of code block
            while i < len(lines) and not lines[i].strip().startswith('```'):
                i += 1

        # Skip tables
        elif line_stripped.startswith('| '):
            story.append(Paragraph('<i>[Table - See markdown file for details]</i>', normal_style))

        # Bullet points
        elif line_stripped.startswith('- '):
            text = line_stripped[2:]
            story.append(Paragraph(f'• {text}', normal_style))

        # Checkboxes
        elif line_stripped.startswith('- [ ]') or line_stripped.startswith('- [x]'):
            text = line_stripped.replace('- [ ]', '[ ]').replace('- [x]', '[x]')
            story.append(Paragraph(text, normal_style))

        # Regular text
        elif line_stripped and not any(line_stripped.startswith(c) for c in ['#', '|', '`', '-', '*']):
            if len(line_stripped) > 2:
                story.append(Paragraph(line_stripped, normal_style))

    # Build PDF
    doc.build(story)

    # Verify
    if os.path.exists(pdf_file):
        size_mb = os.path.getsize(pdf_file) / (1024*1024)
        print('[OK] PDF created successfully')
        print(f'  File: {pdf_file}')
        print(f'  Size: {size_mb:.2f} MB')
        return True
    else:
        print('[ERROR] PDF creation failed')
        return False

if __name__ == '__main__':
    try:
        create_pdf()
    except ImportError as ie:
        print('[ERROR] reportlab not installed')
        print('Install with: pip install reportlab')
    except Exception as e:
        print(f'[ERROR] {str(e)}')
