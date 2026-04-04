import json
import os
import html
import re
import textwrap
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, 
                                XPreformatted, Table, TableStyle, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_styled_table(data_dict, col_widths=[120, 380]):
    """
    Converts a dictionary into a professionally styled ReportLab Table.
    Matches standard VAPT reporting formats with dark headers and gridlines.
    """
    if not data_dict:
        return Table([["No data available", ""]])

    # Header Row
    data = [["Parameter", "Description"]]
    
    for key, value in data_dict.items():
        # Clean up the key for display
        display_key = str(key).replace('_', ' ').title()
        
        # Pretty-print nested JSON if the value is complex
        if isinstance(value, (dict, list)):
            display_val = json.dumps(value, indent=2)
        else:
            display_val = str(value)
            
        # Wrap very long strings in tables to prevent column overflow
        wrapped_val = '\n'.join([textwrap.fill(line, width=65) for line in display_val.split('\n')])
        data.append([display_key, wrapped_val])

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f497d')), # Dark Blue Header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f2f2f2')), # Light Gray Body
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (1, 1), (-1, -1), 'Courier'), # Courier for technical values
        ('FONTSIZE', (1, 1), (-1, -1), 8),
    ]))
    return t

def parse_ai_markdown(text, styles):
    """
    Parses Markdown text from the AI into ReportLab Flowables.
    Handles headings, bold text, italics, inline code, bullet points, and word-wrapped code blocks.
    """
    elements = []
    lines = text.split('\n')
    in_code_block = False
    code_content = []
    
    # Custom style for AI code blocks
    code_style = ParagraphStyle(
        'CodeBlock', 
        parent=styles['Normal'], 
        fontName='Courier', 
        fontSize=8, 
        leading=10, 
        backColor=colors.HexColor('#e8e8e8'), 
        borderColor=colors.HexColor('#cccccc'),
        borderWidth=1,
        borderPadding=6
    )
    
    # Custom style for bullet points and lists
    list_style = ParagraphStyle(
        'ListStyle', 
        parent=styles['Normal'], 
        leftIndent=20,
        spaceBefore=3,
        spaceAfter=3
    )
    
    for line in lines:
        # Detect Code Blocks
        if line.strip().startswith('```'):
            if in_code_block:
                # Close the block and process the code
                code_text = '\n'.join(code_content)
                # Force wrap long payload/shell strings to prevent horizontal overlapping
                wrapped_code = '\n'.join([textwrap.fill(c_line, width=80) for c_line in code_text.split('\n')])
                
                # We still escape HTML here because XPreformatted parses basic XML
                elements.append(XPreformatted(html.escape(wrapped_code), code_style))
                elements.append(Spacer(1, 10))
                in_code_block = False
                code_content = []
            else:
                in_code_block = True
            continue
            
        if in_code_block:
            code_content.append(line)
            continue
            
        # --- Process normal text formatting ---
        # 1. Escape HTML characters first
        safe_line = html.escape(line)
        
        # 2. Apply inline code first (`text`) - Use a simpler tag to avoid nesting issues
        # We use <code> style instead of <font> to keep it cleaner for ReportLab's parser
        safe_line = re.sub(r'`(.*?)`', r'<b>[\1]</b>', safe_line)
        
        # 3. Apply bolding (**text**)
        safe_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_line)
        
        # 4. Apply italics (*text*)
        safe_line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', safe_line)
        
        if not safe_line.strip():
            elements.append(Spacer(1, 5))
            continue
            
        # Handle Headings and Lists
        if safe_line.startswith('### '):
            elements.append(Spacer(1, 10))
            # Clean tags from headings to prevent nested errors in titles
            clean_head = re.sub('<[^>]*>', '', safe_line.replace('### ', ''))
            elements.append(Paragraph(clean_head, styles['Heading3']))
            elements.append(Spacer(1, 5))
        elif safe_line.startswith('## '):
            elements.append(Spacer(1, 15))
            clean_head = re.sub('<[^>]*>', '', safe_line.replace('## ', ''))
            elements.append(Paragraph(clean_head, styles['Heading2']))
            elements.append(Spacer(1, 5))
        elif safe_line.startswith('# '):
            clean_head = re.sub('<[^>]*>', '', safe_line.replace('# ', ''))
            elements.append(Paragraph(clean_head, styles['Heading1']))
        elif safe_line.strip().startswith(('&bull; ', '- ', '* ')): # Handling bullets
            # Clean the marker and treat as bullet
            clean_line = re.sub(r'^(&bull;|-|\*)\s+', '', safe_line.strip())
            elements.append(Paragraph(f"&bull; {clean_line}", list_style))
        elif re.match(r'^\d+\.\s', safe_line.strip()): # Handling numbered lists
            elements.append(Paragraph(safe_line.strip(), list_style))
        else:
            try:
                elements.append(Paragraph(safe_line, styles['Normal']))
            except:
                # Fallback: if tags are still broken, strip them and send plain text
                clean_line = re.sub('<[^>]*>', '', safe_line)
                elements.append(Paragraph(clean_line, styles['Normal']))
            
    return elements

def generate_security_report(url, recon_data, vuln_data, exploit_data, ai_text):
    domain = url.replace("https://", "").replace("http://", "").split("/")[0].replace(":", "_")
    os.makedirs("reports", exist_ok=True)
    report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_filename = f"reports/security_report_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    try:
        doc = SimpleDocTemplate(report_filename, pagesize=letter,
                                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        
        # Custom Title Style for Cover Page
        title_style = ParagraphStyle(
            'CoverTitle', 
            parent=styles['Title'], 
            fontSize=24, 
            spaceAfter=30, 
            textColor=colors.HexColor('#1f497d')
        )

        content = []

        # --- PAGE 1: COVER PAGE ---
        content.append(Spacer(1, 150))
        content.append(Paragraph("AutoPent Vulnerability Assessment", title_style))
        content.append(Paragraph("and Penetration Testing Report", title_style))
        content.append(Spacer(1, 50))
        
        cover_details = {
            "Target URL": url,
            "Assessment Date": report_date,
            "Prepared By": "AutoPent AI Agent"
        }
        content.append(create_styled_table(cover_details))
        content.append(PageBreak())

        # --- PAGE 2: EXECUTIVE SUMMARY & RECONNAISSANCE ---
        content.append(Paragraph("1.0 Executive Summary", styles['Heading1']))
        intro_text = (
            f"This document outlines the findings of the automated security assessment performed on <b>{url}</b>. "
            "The objective of this assessment was to identify potential vulnerabilities, misconfigurations, and "
            "security weaknesses within the target environment using AI-driven orchestration."
        )
        content.append(Paragraph(intro_text, styles['Normal']))
        content.append(Spacer(1, 20))

        content.append(Paragraph("1.1 Reconnaissance Data", styles['Heading2']))
        content.append(create_styled_table(recon_data))
        content.append(PageBreak())

        # --- PAGE 3: VULNERABILITY DETAILS ---
        content.append(Paragraph("2.0 Vulnerability Findings", styles['Heading1']))
        
        # 2.1 AI Fuzzer Results
        content.append(Paragraph("2.1 AI-Driven Intelligent Fuzzing", styles['Heading2']))
        fuzzer_results = vuln_data.get("AI_Fuzzer", [])
        if not fuzzer_results:
            content.append(Paragraph("No vulnerabilities discovered by the intelligent fuzzer.", styles['Normal']))
        else:
            for i, find in enumerate(fuzzer_results):
                content.append(Paragraph(f"Finding #{i+1}: {find.get('vulnerability', 'Unknown')}", styles['Heading3']))
                content.append(create_styled_table(find))
                content.append(Spacer(1, 10))

        # 2.2 Raw Tool Findings
        content.append(Paragraph("2.2 Traditional Tool Scan Results", styles['Heading2']))
        raw_findings = vuln_data.get("Raw_Findings", {})
        if not raw_findings:
            content.append(Paragraph("No significant findings from traditional scanners (Nmap/SQLMap).", styles['Normal']))
        else:
            for tool, output in raw_findings.items():
                content.append(Paragraph(f"Scanner: {tool}", styles['Heading3']))
                code_style = ParagraphStyle('RawCode', parent=styles['Normal'], fontName='Courier', fontSize=7)
                safe_out = html.escape(str(output))
                wrapped_out = '\n'.join([textwrap.fill(line, width=90) for line in safe_out.split('\n')[:100]]) # Limit lines
                content.append(XPreformatted(wrapped_out, code_style))
                content.append(Spacer(1, 10))

        content.append(PageBreak())

        # --- PAGE 4: EXPLOITATION RESULTS ---
        content.append(Paragraph("3.0 Exploitation Results", styles['Heading1']))
        
        exploits_attempted = exploit_data.get("exploits_attempted", [])
        if not exploits_attempted:
            content.append(Paragraph("No exploitation modules were successfully executed.", styles['Normal']))
            if exploit_data.get("message"):
                content.append(Paragraph(f"Status: {exploit_data['message']}", styles['Normal']))
        else:
            status_summary = {
                "Target IP": exploit_data.get("target_ip"),
                "Exploits Found": len(exploits_attempted),
                "Session Opened": exploit_data.get("success", False)
            }
            content.append(create_styled_table(status_summary))
            content.append(Spacer(1, 20))

            for attempt in exploits_attempted:
                mod_name = attempt.get("module", "Unknown")
                content.append(Paragraph(f"Module: {mod_name}", styles['Heading3']))
                content.append(create_styled_table(attempt))
                content.append(Spacer(1, 15))

        content.append(PageBreak())

        # --- PAGE 5: AI REMEDIATION ---
        content.append(Paragraph("4.0 AI-Powered Remediation & Chaining Analysis", styles['Heading1']))
        content.append(Spacer(1, 10))
        
        if ai_text:
            ai_elements = parse_ai_markdown(ai_text, styles)
            content.extend(ai_elements)
        else:
             content.append(Paragraph("AI remediation analysis was unavailable for this session.", styles['Normal']))

        # Build the PDF
        doc.build(content)
        return report_filename
        
    except Exception as e:
        print(f"Report Generation Error: {e}")
        import traceback
        traceback.print_exc()
        return None