from typing import Any, Dict, Optional, Tuple, Union
from flask import jsonify

def format_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    status_code: int = 200,
    meta: Optional[Dict] = None
) -> Tuple[Dict, int]:
    """
    Format API response consistently
    
    Args:
        data: Response data
        message: Optional message
        status_code: HTTP status code
        meta: Optional metadata
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': 200 <= status_code < 300,
        'status_code': status_code
    }
    
    if message:
        response['message'] = message
        
    if data is not None:
        response['data'] = data
        
    if meta:
        response['meta'] = meta
        
    return jsonify(response), status_code

def success_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    status_code: int = 200,
    meta: Optional[Dict] = None
) -> Tuple[Dict, int]:
    """
    Create a success response
    
    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code (default: 200)
        meta: Optional metadata
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    return format_response(
        data=data,
        message=message,
        status_code=status_code,
        meta=meta
    )

def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Union[str, Dict]] = None
) -> Tuple[Dict, int]:
    """
    Create an error response
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        error_code: Optional error code
        details: Optional error details
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    error_data = {
        'message': message
    }
    
    if error_code:
        error_data['code'] = error_code
        
    if details:
        error_data['details'] = details
        
    return format_response(
        data={'error': error_data},
        status_code=status_code
    )

def pagination_meta(
    page: int,
    per_page: int,
    total: int,
    pages: int
) -> Dict:
    """
    Create pagination metadata
    
    Args:
        page: Current page number
        per_page: Items per page
        total: Total number of items
        pages: Total number of pages
        
    Returns:
        Dictionary with pagination metadata
    """
    return {
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages
        }
    }

def blockchain_meta(
    tx_hash: Optional[str] = None,
    block_number: Optional[int] = None,
    gas_used: Optional[int] = None,
    contract_address: Optional[str] = None
) -> Dict:
    """
    Create blockchain transaction metadata
    
    Args:
        tx_hash: Transaction hash
        block_number: Block number
        gas_used: Gas used
        contract_address: Contract address
        
    Returns:
        Dictionary with blockchain metadata
    """
    meta = {}
    
    if tx_hash:
        meta['transaction_hash'] = tx_hash
    if block_number:
        meta['block_number'] = block_number
    if gas_used:
        meta['gas_used'] = gas_used
    if contract_address:
        meta['contract_address'] = contract_address
        
    return {'blockchain': meta}

def storage_meta(
    cid: str,
    filename: Optional[str] = None,
    size: Optional[int] = None,
    mime_type: Optional[str] = None
) -> Dict:
    """
    Create storage metadata
    
    Args:
        cid: IPFS CID
        filename: Original filename
        size: File size in bytes
        mime_type: File MIME type
        
    Returns:
        Dictionary with storage metadata
    """
    meta = {'cid': cid}
    
    if filename:
        meta['filename'] = filename
    if size:
        meta['size'] = size
    if mime_type:
        meta['mime_type'] = mime_type
        
    return {'storage': meta}
