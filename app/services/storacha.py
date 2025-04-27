import requests
from flask import current_app
import json
from typing import Optional, Union
from werkzeug.datastructures import FileStorage
import io

class StorachaClient:
    """Client for interacting with Storacha IPFS service"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        
    def upload_file(self, file: FileStorage) -> Optional[str]:
        """
        Upload a file to Storacha
        
        Args:
            file: File object to upload
            
        Returns:
            str: IPFS CID if successful, None otherwise
        """
        try:
            # Create multipart form data
            files = {
                'file': (file.filename, file.stream, file.content_type)
            }
            
            response = requests.post(
                'https://api.storacha.io/upload',
                headers=self.headers,
                files=files
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get('cid')
            
        except Exception as e:
            current_app.logger.error(f"Storacha upload failed: {str(e)}")
            return None
            
    def upload_content(self, content: Union[str, bytes], filename: str) -> Optional[str]:
        """
        Upload content directly to Storacha
        
        Args:
            content: String or bytes content to upload
            filename: Name for the uploaded file
            
        Returns:
            str: IPFS CID if successful, None otherwise
        """
        try:
            if isinstance(content, str):
                content = content.encode('utf-8')
                
            # Create file-like object
            file_obj = io.BytesIO(content)
            
            files = {
                'file': (filename, file_obj, 'application/octet-stream')
            }
            
            response = requests.post(
                'https://api.storacha.io/upload',
                headers=self.headers,
                files=files
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get('cid')
            
        except Exception as e:
            current_app.logger.error(f"Storacha content upload failed: {str(e)}")
            return None
            
    def get_content(self, cid: str) -> Optional[bytes]:
        """
        Retrieve content from Storacha by CID
        
        Args:
            cid: IPFS CID to retrieve
            
        Returns:
            bytes: File content if successful, None otherwise
        """
        try:
            response = requests.get(
                f'https://api.storacha.io/content/{cid}',
                headers=self.headers
            )
            
            response.raise_for_status()
            return response.content
            
        except Exception as e:
            current_app.logger.error(f"Storacha content retrieval failed: {str(e)}")
            return None
            
    def check_cid_availability(self, cid: str) -> bool:
        """
        Check if a CID is available on IPFS
        
        Args:
            cid: IPFS CID to check
            
        Returns:
            bool: True if available, False otherwise
        """
        try:
            response = requests.head(
                f'https://api.storacha.io/content/{cid}',
                headers=self.headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            current_app.logger.error(f"Storacha availability check failed: {str(e)}")
            return False
            
    def get_metadata(self, cid: str) -> Optional[dict]:
        """
        Get metadata for a CID
        
        Args:
            cid: IPFS CID to get metadata for
            
        Returns:
            dict: Metadata if successful, None otherwise
        """
        try:
            response = requests.get(
                f'https://api.storacha.io/metadata/{cid}',
                headers=self.headers
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            current_app.logger.error(f"Storacha metadata retrieval failed: {str(e)}")
            return None
            
    def pin_cid(self, cid: str) -> bool:
        """
        Pin a CID to ensure it remains available
        
        Args:
            cid: IPFS CID to pin
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f'https://api.storacha.io/pin/{cid}',
                headers=self.headers
            )
            
            response.raise_for_status()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Storacha pinning failed: {str(e)}")
            return False
