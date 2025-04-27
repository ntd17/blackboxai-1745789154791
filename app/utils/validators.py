import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_user_input(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate user registration input"""
    required_fields = ['name', 'email', 'password']
    
    # Check required fields
    if not all(field in data for field in required_fields):
        return False, f"Missing required fields: {', '.join(required_fields)}"
    
    # Validate email
    if not validate_email(data['email']):
        return False, "Invalid email format"
    
    # Validate name length
    if len(data['name'].strip()) < 2:
        return False, "Name must be at least 2 characters long"
    
    # Validate password strength
    if len(data['password']) < 8:
        return False, "Password must be at least 8 characters long"
    
    return True, None

def validate_contract_input(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate contract generation input"""
    required_fields = [
        'creator_id', 'title', 'location', 'planned_start_date',
        'planned_duration_days', 'contractor_details', 'provider_details',
        'payment_details'
    ]
    
    # Check required fields
    if not all(field in data for field in required_fields):
        return False, f"Missing required fields: {', '.join(required_fields)}"
    
    # Validate location
    location = data.get('location', {})
    if not all(key in location for key in ['city', 'state']):
        return False, "Location must include city and state"
    
    if 'coordinates' in location:
        coords = location['coordinates']
        if not all(key in coords for key in ['lat', 'lon']):
            return False, "Coordinates must include lat and lon"
    
    # Validate date format
    try:
        datetime.strptime(data['planned_start_date'], '%Y-%m-%d')
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD"
    
    # Validate duration
    if not isinstance(data['planned_duration_days'], int) or data['planned_duration_days'] < 1:
        return False, "Duration must be a positive integer"
    
    # Validate contractor and provider details
    for party in ['contractor_details', 'provider_details']:
        details = data.get(party, {})
        if not all(key in details for key in ['name', 'email']):
            return False, f"{party} must include name and email"
        if not validate_email(details['email']):
            return False, f"Invalid email in {party}"
    
    # Validate payment details
    payment = data.get('payment_details', {})
    if not all(key in payment for key in ['amount', 'method']):
        return False, "Payment details must include amount and method"
    
    if not isinstance(payment['amount'], (int, float)) or payment['amount'] <= 0:
        return False, "Payment amount must be a positive number"
    
    return True, None

def validate_signature_input(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate contract signature input"""
    required_fields = ['signer_email', 'signature_data']
    
    # Check required fields
    if not all(field in data for field in required_fields):
        return False, f"Missing required fields: {', '.join(required_fields)}"
    
    # Validate email
    if not validate_email(data['signer_email']):
        return False, "Invalid signer email format"
    
    # Validate signature data
    sig_data = data.get('signature_data', {})
    if not isinstance(sig_data, dict):
        return False, "Signature data must be an object"
    
    if 'signature' not in sig_data:
        return False, "Signature data must include signature"
    
    if 'timestamp' in sig_data:
        try:
            datetime.fromisoformat(sig_data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            return False, "Invalid timestamp format. Use ISO 8601"
    
    return True, None

def validate_cid(cid: str) -> bool:
    """Validate IPFS CID format"""
    # Basic CID format validation
    pattern = r'^Qm[1-9A-HJ-NP-Za-km-z]{44}$'
    return bool(re.match(pattern, cid))
