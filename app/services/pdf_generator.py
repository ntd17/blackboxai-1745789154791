from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
from typing import Dict, Optional
import PyPDF2

def generate_contract_pdf(contract: 'Contract', weather_prediction: Optional['WeatherPrediction'] = None) -> bytes:
    """
    Generate a PDF contract document
    
    Args:
        contract: Contract instance
        weather_prediction: Optional WeatherPrediction instance
        
    Returns:
        bytes: Generated PDF content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12
    )
    normal_style = styles['Normal']
    
    # Build document content
    story = []
    
    # Title
    story.append(Paragraph("PAINTING SERVICE CONTRACT", title_style))
    story.append(Spacer(1, 12))
    
    # Contract ID and Date
    story.append(Paragraph(f"Contract ID: {contract.id}", normal_style))
    story.append(Paragraph(f"Date: {datetime.utcnow().strftime('%B %d, %Y')}", normal_style))
    story.append(Spacer(1, 20))
    
    # Parties
    story.append(Paragraph("PARTIES", heading_style))
    story.append(Paragraph(
        f"<b>Contractor:</b> {contract.contractor_name}<br/>"
        f"Email: {contract.contractor_email}",
        normal_style
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"<b>Service Provider:</b> {contract.provider_name}<br/>"
        f"Email: {contract.provider_email}",
        normal_style
    ))
    story.append(Spacer(1, 20))
    
    # Service Details
    story.append(Paragraph("SERVICE DETAILS", heading_style))
    story.append(Paragraph(f"<b>Title:</b> {contract.title}", normal_style))
    if contract.description:
        story.append(Paragraph(f"<b>Description:</b> {contract.description}", normal_style))
    story.append(Spacer(1, 12))
    
    # Location
    location = contract.location
    address = f"{location.get('street', '')}, {location.get('city', '')}, {location.get('state', '')}"
    story.append(Paragraph(f"<b>Location:</b> {address}", normal_style))
    story.append(Spacer(1, 12))
    
    # Timeline
    story.append(Paragraph("TIMELINE", heading_style))
    story.append(Paragraph(
        f"<b>Start Date:</b> {contract.planned_start_date.strftime('%B %d, %Y')}",
        normal_style
    ))
    
    # Duration with weather adjustment if available
    if weather_prediction and contract.adjusted_duration_days:
        story.append(Paragraph(
            f"<b>Original Duration:</b> {contract.planned_duration_days} days<br/>"
            f"<b>Weather-Adjusted Duration:</b> {contract.adjusted_duration_days} days",
            normal_style
        ))
        story.append(Spacer(1, 12))
        
        # Weather Analysis
        story.append(Paragraph("WEATHER ANALYSIS", heading_style))
        story.append(Paragraph(
            f"Based on weather forecast analysis:<br/>"
            f"• Rain Probability: {weather_prediction.rain_probability:.1%}<br/>"
            f"• Predicted Delay: {weather_prediction.predicted_delay_days} days<br/>"
            f"• Confidence Score: {weather_prediction.confidence_score:.1%}",
            normal_style
        ))
    else:
        story.append(Paragraph(
            f"<b>Duration:</b> {contract.planned_duration_days} days",
            normal_style
        ))
    story.append(Spacer(1, 20))
    
    # Payment Terms
    story.append(Paragraph("PAYMENT TERMS", heading_style))
    story.append(Paragraph(
        f"<b>Amount:</b> ${contract.amount:,.2f}<br/>"
        f"<b>Payment Method:</b> {contract.payment_method}",
        normal_style
    ))
    story.append(Spacer(1, 20))
    
    # Terms and Conditions
    story.append(Paragraph("TERMS AND CONDITIONS", heading_style))
    terms = [
        "1. The Service Provider agrees to complete the painting work according to the specifications provided.",
        "2. The Contractor agrees to provide necessary access to the premises during the agreed working hours.",
        "3. Any changes to the scope of work must be agreed upon in writing by both parties.",
        "4. The Service Provider shall maintain appropriate insurance coverage throughout the project.",
        "5. Payment shall be made according to the agreed schedule upon satisfactory completion of work.",
    ]
    for term in terms:
        story.append(Paragraph(term, normal_style))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 20))
    
    # Signatures
    story.append(Paragraph("SIGNATURES", heading_style))
    signature_data = [
        ['Contractor:', 'Service Provider:'],
        ['_' * 30, '_' * 30],
        [contract.contractor_name, contract.provider_name],
        ['Date: _' * 20, 'Date: _' * 20]
    ]
    signature_table = Table(signature_data, colWidths=[doc.width/2.0]*2)
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0, colors.white),
        ('LINEBELOW', (0,1), (-1,1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(signature_table)
    
    # Build PDF
    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

def add_signature_to_pdf(pdf_content: bytes, signature_data: Dict,
                        metadata: Dict) -> bytes:
    """
    Add signature and metadata to an existing PDF
    
    Args:
        pdf_content: Original PDF content
        signature_data: Signature information
        metadata: Additional metadata to add
        
    Returns:
        bytes: Modified PDF content
    """
    # Create PDF reader and writer
    reader = PyPDF2.PdfReader(BytesIO(pdf_content))
    writer = PyPDF2.PdfWriter()
    
    # Copy all pages
    for page in reader.pages:
        writer.add_page(page)
    
    # Add metadata
    writer.add_metadata({
        '/Signed': 'True',
        '/SignatureDate': metadata['timestamp'],
        '/SignerEmail': metadata['signer_email'],
        '/SignerIP': metadata['ip_address']
    })
    
    # Create output buffer
    output = BytesIO()
    writer.write(output)
    
    return output.getvalue()
