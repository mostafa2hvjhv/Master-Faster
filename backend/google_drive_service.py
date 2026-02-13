from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io
import os
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class GoogleDriveService:
    """Service class for Google Drive API operations"""
    
    # Define required API scopes
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_file: str, folder_id: Optional[str] = None):
        """
        Initialize Google Drive service with service account credentials.
        
        Args:
            credentials_file: Path to service account JSON credentials
            folder_id: Default folder ID for backup operations
        """
        self.folder_id = folder_id
        self.credentials_file = credentials_file
        self.service = self._build_service()
        logger.info(f"Google Drive service initialized")
    
    def _build_service(self):
        """Build and return authenticated Drive API service"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.SCOPES
            )
            service = build('drive', 'v3', credentials=credentials)
            logger.info("Successfully authenticated with Google Drive API")
            return service
        except Exception as e:
            logger.error(f"Failed to build Drive service: {str(e)}")
            raise
    
    def create_folder(
        self, 
        folder_name: str,
        parent_folder_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create a new folder in Google Drive.
        
        Args:
            folder_name: Name for new folder
            parent_folder_id: Parent folder ID (optional)
            
        Returns:
            Dict containing folder ID and name
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            logger.info(f"Folder created: {folder.get('name')} (ID: {folder.get('id')})")
            return {
                'id': folder.get('id'),
                'name': folder.get('name'),
                'webViewLink': folder.get('webViewLink')
            }
            
        except HttpError as error:
            logger.error(f"Failed to create folder: {str(error)}")
            raise
    
    def find_folder_by_name(self, folder_name: str) -> Optional[Dict]:
        """
        Find a folder by name.
        
        Args:
            folder_name: Name of folder to find
            
        Returns:
            Dict with folder info or None if not found
        """
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, webViewLink)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                folder = files[0]
                logger.info(f"Found folder: {folder.get('name')} (ID: {folder.get('id')})")
                return folder
            else:
                logger.info(f"Folder '{folder_name}' not found")
                return None
                
        except HttpError as error:
            logger.error(f"Failed to find folder: {str(error)}")
            raise
    
    def get_or_create_folder(self, folder_name: str) -> Dict[str, str]:
        """
        Get existing folder or create new one.
        
        Args:
            folder_name: Name of folder
            
        Returns:
            Dict containing folder ID and name
        """
        folder = self.find_folder_by_name(folder_name)
        
        if folder:
            return folder
        else:
            return self.create_folder(folder_name)
    
    def upload_file(
        self, 
        file_path: str, 
        file_name: Optional[str] = None,
        folder_id: Optional[str] = None,
        mime_type: str = 'application/octet-stream'
    ) -> Dict[str, str]:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Local path to file to upload
            file_name: Name for file in Drive (defaults to local filename)
            folder_id: Target folder ID (defaults to instance folder_id)
            mime_type: MIME type of file
            
        Returns:
            Dict containing file ID and web view link
            
        Raises:
            HttpError: If upload fails
        """
        try:
            if not file_name:
                file_name = os.path.basename(file_path)
            
            target_folder_id = folder_id or self.folder_id
            
            file_metadata = {
                'name': file_name,
                'mimeType': mime_type
            }
            
            if target_folder_id:
                file_metadata['parents'] = [target_folder_id]
            
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )
            
            # Use supportsAllDrives=True for shared folders
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,size,createdTime',
                supportsAllDrives=True
            ).execute()
            
            logger.info(f"File uploaded successfully: {file.get('name')} (ID: {file.get('id')})")
            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'webViewLink': file.get('webViewLink'),
                'size': file.get('size'),
                'createdTime': file.get('createdTime')
            }
            
        except HttpError as error:
            logger.error(f"Failed to upload file: {str(error)}")
            raise
    
    def download_file(
        self, 
        file_id: str, 
        destination_path: str
    ) -> str:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            destination_path: Local path to save downloaded file
            
        Returns:
            Path to downloaded file
            
        Raises:
            HttpError: If download fails
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            fh = io.FileIO(destination_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download progress: {int(status.progress() * 100)}%")
            
            fh.close()
            logger.info(f"File downloaded successfully to: {destination_path}")
            return destination_path
            
        except HttpError as error:
            logger.error(f"Failed to download file: {str(error)}")
            raise
    
    def list_files(
        self, 
        folder_id: Optional[str] = None,
        page_size: int = 100,
        query: Optional[str] = None
    ) -> List[Dict]:
        """
        List files in a folder.
        
        Args:
            folder_id: Folder ID to list files from
            page_size: Maximum number of files to return
            query: Additional query parameters
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            target_folder_id = folder_id or self.folder_id
            
            # Build query
            if target_folder_id:
                q = f"'{target_folder_id}' in parents and trashed=false"
            else:
                q = "trashed=false"
                
            if query:
                q += f" and {query}"
            
            results = self.service.files().list(
                q=q,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
                orderBy="createdTime desc"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} files")
            return files
            
        except HttpError as error:
            logger.error(f"Failed to list files: {str(error)}")
            raise
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive.
        
        Args:
            file_id: ID of file to delete
            
        Returns:
            True if successful
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"File deleted: {file_id}")
            return True
            
        except HttpError as error:
            logger.error(f"Failed to delete file: {str(error)}")
            raise
    
    def get_file_metadata(self, file_id: str) -> Dict:
        """
        Get metadata for a specific file.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Dict containing file metadata
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,createdTime,modifiedTime,webViewLink'
            ).execute()
            
            logger.info(f"Retrieved metadata for file: {file.get('name')}")
            return file
            
        except HttpError as error:
            logger.error(f"Failed to get file metadata: {str(error)}")
            raise
