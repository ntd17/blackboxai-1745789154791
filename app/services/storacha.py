import os
import requests
from flask import current_app
import json
from typing import Optional, Union, Dict
from werkzeug.datastructures import FileStorage
import io
import logging

logger = logging.getLogger(__name__)

class StorachaError(Exception):
    """Base exception for Storacha client errors"""
    pass

class StorachaAuthError(StorachaError):
    """Authentication error with Storacha API"""
    pass

class StorachaClient:
    """Client for interacting with Storacha IPFS service with bridge token authentication"""
    
    def __init__(self):
        self.x_auth_secret = os.getenv('STORACHA_X_AUTH_SECRET')
        self.auth_token = os.getenv('STORACHA_AUTHORIZATION_TOKEN')
        
        if not self.x_auth_secret or not self.auth_token:
            raise StorachaAuthError("Missing Storacha authentication credentials")
        
        self.base_url = 'https://api.storacha.io'
        self.headers = {
            'X-Auth-Secret': self.x_auth_secret,
            'Authorization': self.auth_token,
            'Accept': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an authenticated request to Storacha API
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments
            
        Returns:
            Response object
            
        Raises:
            StorachaAuthError: If authentication fails
            StorachaError: For other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Ensure headers are included
        if 'headers' in kwargs:
            kwargs['headers'].update(self.headers)
        else:
            kwargs['headers'] = self.headers
        
        try:
            response = requests.request(method, url, **kwargs)
            
            # Handle authentication errors
            if response.status_code == 401:
                logger.error("Storacha authentication failed")
                raise StorachaAuthError("Invalid authentication credentials")
            
            # Handle other errors
            if response.status_code >= 400:
                logger.error(f"Storacha API error: {response.text}")
                raise StorachaError(f"API request failed: {response.status_code}")
            
            return response
            
        except requests.RequestException as e:
            logger.error(f"Request to Storacha failed: {str(e)}")
            raise StorachaError(f"Request failed: {str(e)}")
    
    def upload_file(self, file: FileStorage) -> Optional[str]:
        """
        Upload a file to Storacha
        
        Args:
            file: File object to upload
            
        Returns:
            str: IPFS CID if successful, None otherwise
            
        Raises:
            StorachaAuthError: If authentication fails
            StorachaError: For other upload errors
        """
        try:
            logger.info(f"Uploading file: {file.filename}")
            
            files = {
                'file': (file.filename, file.stream, file.content_type)
            }
            
            response = self._make_request('POST', '/upload', files=files)
            result = response.json()
            
            if 'cid' not in result:
                raise StorachaError("No CID in response")
            
            logger.info(f"File uploaded successfully. CID: {result['cid']}")
            return result['cid']
            
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise
    
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
            logger.info(f"Uploading content as: {filename}")
            
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            file_obj = io.BytesIO(content)
            files = {
                'file': (filename, file_obj, 'application/octet-stream')
            }
            
            response = self._make_request('POST', '/upload', files=files)
            result = response.json()
            
            if 'cid' not in result:
                raise StorachaError("No CID in response")
            
            logger.info(f"Content uploaded successfully. CID: {result['cid']}")
            return result['cid']
            
        except Exception as e:
            logger.error(f"Content upload failed: {str(e)}")
            raise
    
    def get_content(self, cid: str) -> Optional[bytes]:
        """
        Retrieve content from Storacha by CID
        
        Args:
            cid: IPFS CID to retrieve
            
        Returns:
            bytes: File content if successful, None otherwise
        """
        try:
            logger.info(f"Retrieving content for CID: {cid}")
            
            response = self._make_request('GET', f'/content/{cid}')
            return response.content
            
        except Exception as e:
            logger.error(f"Content retrieval failed: {str(e)}")
            raise
    
    def check_cid_availability(self, cid: str) -> bool:
        """
        Check if a CID is available on IPFS
        
        Args:
            cid: IPFS CID to check
            
        Returns:
            bool: True if available, False otherwise
        """
        try:
            logger.info(f"Checking availability of CID: {cid}")
            
            response = self._make_request('HEAD', f'/content/{cid}')
            return response.status_code == 200
            
        except StorachaError:
            return False
        except Exception as e:
            logger.error(f"CID availability check failed: {str(e)}")
            return False
    
    def get_metadata(self, cid: str) -> Optional[Dict]:
        """
        Get metadata for a CID
        
        Args:
            cid: IPFS CID to get metadata for
            
        Returns:
            dict: Metadata if successful, None otherwise
        """
        try:
            logger.info(f"Retrieving metadata for CID: {cid}")
            
            response = self._make_request('GET', f'/metadata/{cid}')
            return response.json()
            
        except Exception as e:
            logger.error(f"Metadata retrieval failed: {str(e)}")
            raise
    
    def pin_cid(self, cid: str) -> bool:
        """
        Pin a CID to ensure it remains available
        
        Args:
            cid: IPFS CID to pin
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Pinning CID: {cid}")
            
            response = self._make_request('POST', f'/pin/{cid}')
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"CID pinning failed: {str(e)}")
            return False
