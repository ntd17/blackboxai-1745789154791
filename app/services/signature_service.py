import secrets
import jwt
import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509 import load_pem_x509_certificate
from endesive import pdf
import io

class SignatureService:
    def __init__(self, app_config):
        self.config = app_config
        self.token_expiry = int(app_config.get('TOKEN_EXPIRY_MINUTES', 30))
        self.secret_key = app_config['SECRET_KEY']

    def generate_email_token(self, email, cpf):
        """Generate a secure token for email verification"""
        token = secrets.token_urlsafe(32)
        expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=self.token_expiry)
        
        # Create JWT with token, email, and CPF
        token_data = {
            'token': token,
            'email': email,
            'cpf': cpf,
            'exp': expiry
        }
        
        jwt_token = jwt.encode(token_data, self.secret_key, algorithm='HS256')
        return jwt_token, expiry

    def validate_email_token(self, jwt_token):
        """Validate the email verification token"""
        try:
            token_data = jwt.decode(jwt_token, self.secret_key, algorithms=['HS256'])
            return token_data
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    def validate_icp_certificate(self, cert_data):
        """Validate ICP-Brasil certificate"""
        try:
            cert = load_pem_x509_certificate(cert_data)
            
            # Verify certificate chain
            # TODO: Implement ICP-Brasil chain validation
            
            # Extract certificate info
            subject = cert.subject
            issuer = cert.issuer
            valid_from = cert.not_valid_before
            valid_until = cert.not_valid_after
            
            return {
                'subject': str(subject),
                'issuer': str(issuer),
                'valid_from': valid_from.isoformat(),
                'valid_until': valid_until.isoformat(),
                'is_valid': True
            }
        except Exception as e:
            raise ValueError(f"Invalid certificate: {str(e)}")

    def sign_pdf_with_certificate(self, pdf_content, cert_data, password):
        """Sign PDF using ICP-Brasil certificate"""
        try:
            # Load the certificate and private key (kept in memory only)
            p12 = serialization.load_pem_private_key(
                cert_data,
                password=password.encode(),
            )
            
            # Create signature
            date = datetime.datetime.utcnow()
            signature = pdf.cms.sign(
                pdf_content,
                p12,
                'sha256',
                'Documento assinado digitalmente com certificado ICP-Brasil',
                'Assinatura Digital',
                location='Brasil',
                signingdate=date,
            )
            
            # Create signed PDF
            signed_pdf = pdf.cms.sign(
                pdf_content,
                signature,
                'sha256',
                output_type='pdf'
            )
            
            return signed_pdf
            
        except Exception as e:
            raise ValueError(f"Error signing PDF: {str(e)}")

    def verify_pdf_signature(self, signed_pdf):
        """Verify PDF signature"""
        try:
            # Extract and verify signature
            signatures = pdf.cms.verify(signed_pdf)
            
            if not signatures:
                return False, "No signature found"
            
            # Verify each signature
            results = []
            for signature in signatures:
                cert = signature[1]
                valid = self.validate_icp_certificate(cert)
                results.append(valid)
            
            return True, results
            
        except Exception as e:
            return False, str(e)

    def get_signature_metadata(self, method, **kwargs):
        """Generate signature metadata based on method"""
        metadata = {
            'method': method,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'ip_address': kwargs.get('ip_address'),
        }
        
        if method == 'token_email':
            metadata.update({
                'email': kwargs.get('email'),
                'cpf': kwargs.get('cpf'),
                'token_verified': True
            })
        elif method in ['icp_upload', 'icp_direct']:
            metadata.update({
                'certificate_info': kwargs.get('certificate_info'),
                'signature_type': 'ICP-Brasil'
            })
            
        return metadata
