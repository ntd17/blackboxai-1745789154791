import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import current_app, render_template_string
from typing import Optional, List
import os

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.smtp_server = current_app.config['SMTP_SERVER']
        self.smtp_port = current_app.config['SMTP_PORT']
        self.username = current_app.config['SMTP_USERNAME']
        self.password = current_app.config['SMTP_PASSWORD']
        
    def send_email(self, to_email: str, subject: str, html_content: str,
                   attachments: Optional[List[tuple]] = None) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            attachments: Optional list of (filename, content) tuples
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Add attachments if any
            if attachments:
                for filename, content in attachments:
                    attachment = MIMEApplication(content, _subtype="pdf")
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
            return False

def send_contract_email(recipient_email: str, contract: 'Contract', cid: str):
    """
    Send contract notification email
    
    Args:
        recipient_email: Recipient's email address
        contract: Contract instance
        cid: IPFS CID of the contract
    """
    email_service = EmailService()
    
    # Contract review link
    review_link = f"https://app.example.com/contracts/review/{cid}"
    
    # Email template
    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Contract Review Request</h2>
        <p>Hello,</p>
        <p>You have received a new painting contract for review and signature.</p>
        
        <h3>Contract Details:</h3>
        <ul>
            <li><strong>Title:</strong> {{ contract.title }}</li>
            <li><strong>Location:</strong> {{ contract.location.city }}, {{ contract.location.state }}</li>
            <li><strong>Start Date:</strong> {{ contract.planned_start_date }}</li>
            <li><strong>Duration:</strong> {{ contract.planned_duration_days }} days</li>
            {% if contract.adjusted_duration_days %}
            <li><strong>Adjusted Duration:</strong> {{ contract.adjusted_duration_days }} days (based on weather forecast)</li>
            {% endif %}
        </ul>
        
        <p>Please review and sign the contract using the link below:</p>
        <p>
            <a href="{{ review_link }}" style="
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                display: inline-block;
            ">Review Contract</a>
        </p>
        
        <p style="margin-top: 20px;">
            <small>
                This contract is stored securely on IPFS with CID: {{ cid }}<br>
                All signatures are recorded on the blockchain for verification.
            </small>
        </p>
    </body>
    </html>
    """
    
    # Render template
    email_content = render_template_string(
        html_content,
        contract=contract,
        review_link=review_link,
        cid=cid
    )
    
    # Send email
    email_service.send_email(
        to_email=recipient_email,
        subject=f"Painting Contract for Review - {contract.title}",
        html_content=email_content
    )

def send_signature_confirmation(contract: 'Contract'):
    """
    Send signature confirmation emails to all parties
    
    Args:
        contract: Signed contract instance
    """
    email_service = EmailService()
    
    # Email template
    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Contract Signature Confirmed</h2>
        <p>Hello,</p>
        <p>The painting contract has been successfully signed by all parties.</p>
        
        <h3>Contract Details:</h3>
        <ul>
            <li><strong>Title:</strong> {{ contract.title }}</li>
            <li><strong>Location:</strong> {{ contract.location.city }}, {{ contract.location.state }}</li>
            <li><strong>Start Date:</strong> {{ contract.planned_start_date }}</li>
            <li><strong>Duration:</strong> {{ contract.adjusted_duration_days or contract.planned_duration_days }} days</li>
            <li><strong>Signed Date:</strong> {{ contract.signature_date }}</li>
        </ul>
        
        <p>You can view the signed contract using the link below:</p>
        <p>
            <a href="https://app.example.com/contracts/view/{{ contract.signed_cid }}" style="
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                display: inline-block;
            ">View Signed Contract</a>
        </p>
        
        <p style="margin-top: 20px;">
            <small>
                The signed contract is stored on IPFS with CID: {{ contract.signed_cid }}<br>
                The signature has been recorded on the blockchain for verification.
                Transaction hash: {{ contract.blockchain_tx }}
            </small>
        </p>
    </body>
    </html>
    """
    
    # Send to both parties
    for email in [contract.contractor_email, contract.provider_email]:
        email_content = render_template_string(
            html_content,
            contract=contract
        )
        
        email_service.send_email(
            to_email=email,
            subject=f"Contract Signed - {contract.title}",
            html_content=email_content
        )
