"""
File Manager - Handles file operations for .lakra format files.
"""

import os
import json
from typing import Tuple, Dict, Any, Optional
from metadata_manager import MetadataManager

class FileManager:
    """Manages file operations for GhostKey files."""
    
    def __init__(self):
        self.metadata_manager = MetadataManager()
        
    def is_lakra_file(self, file_path: str) -> bool:
        """Check if a file is a .lakra format file."""
        return file_path.endswith('.lakra')
    
    def get_base_format(self, file_path: str) -> Optional[str]:
        """Get the base format from a .lakra file (e.g., 'txt' from 'file.txt.lakra')."""
        if not self.is_lakra_file(file_path):
            return None
        
        # Remove .lakra extension and get the previous extension
        base_path = file_path[:-6]  # Remove '.lakra'
        if '.' in base_path:
            return base_path.split('.')[-1].lower()
        return 'txt'  # Default to txt if no base extension
    
    def suggest_lakra_filename(self, original_path: str) -> str:
        """Suggest a .lakra filename based on the original file path."""
        if self.is_lakra_file(original_path):
            return original_path
        return original_path + '.lakra'
    
    def load_file(self, file_path: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Load content and metadata from a file."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
            
            if self.is_lakra_file(file_path):
                return self._parse_lakra_content(file_content)
            else:
                # Regular file, no metadata
                return file_content, None
        
        except Exception as e:
            raise Exception(f"Failed to load file '{file_path}': {str(e)}")
    
    def save_file(self, file_path: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Save content and metadata to a file."""
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            if self.is_lakra_file(file_path):
                file_content = self._create_lakra_content(content, metadata)
            else:
                file_content = content
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(file_content)
        
        except Exception as e:
            raise Exception(f"Failed to save file '{file_path}': {str(e)}")
    
    def _parse_lakra_content(self, file_content: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Parse .lakra file content to extract text content and metadata."""
        try:
            # Look for metadata delimiter
            metadata_start = "<!-- GHOSTKEY_METADATA_START -->"
            metadata_end = "<!-- GHOSTKEY_METADATA_END -->"
            
            metadata_start_idx = file_content.find(metadata_start)
            
            if metadata_start_idx == -1:
                # No metadata found, return content as-is
                return file_content, None
            
            # Extract content (everything before metadata)
            content = file_content[:metadata_start_idx].rstrip()
            
            # Find metadata end
            metadata_start_idx += len(metadata_start)
            metadata_end_idx = file_content.find(metadata_end, metadata_start_idx)
            
            if metadata_end_idx == -1:
                # Malformed metadata, return content without metadata
                return content, None
            
            # Extract metadata JSON
            metadata_json = file_content[metadata_start_idx:metadata_end_idx].strip()
            
            # Parse metadata
            metadata = self.metadata_manager.deserialize_metadata(metadata_json)
            
            return content, metadata
        
        except Exception as e:
            print(f"Error parsing lakra content: {e}")
            # Return content without metadata on error
            return file_content, None
    
    def _create_lakra_content(self, content: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Create .lakra file content with embedded metadata."""
        try:
            # Start with the text content
            lakra_content = content
            
            # Add metadata if provided
            if metadata:
                # Validate metadata
                if self.metadata_manager.validate_metadata(metadata):
                    metadata_json = self.metadata_manager.serialize_metadata(metadata)
                    
                    # Add metadata section
                    lakra_content += "\n\n<!-- GHOSTKEY_METADATA_START -->\n"
                    lakra_content += metadata_json
                    lakra_content += "\n<!-- GHOSTKEY_METADATA_END -->"
                else:
                    print("Warning: Invalid metadata, saving without metadata")
            
            return lakra_content
        
        except Exception as e:
            print(f"Error creating lakra content: {e}")
            return content
    
    def export_metadata(self, file_path: str, metadata: Dict[str, Any]):
        """Export metadata to a separate .meta file."""
        try:
            meta_file_path = file_path + ".meta"
            metadata_json = self.metadata_manager.serialize_metadata(metadata)
            
            with open(meta_file_path, 'w', encoding='utf-8') as file:
                file.write(metadata_json)
        
        except Exception as e:
            raise Exception(f"Failed to export metadata: {str(e)}")
    
    def import_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Import metadata from a separate .meta file."""
        try:
            meta_file_path = file_path + ".meta"
            
            if not os.path.exists(meta_file_path):
                return None
            
            with open(meta_file_path, 'r', encoding='utf-8') as file:
                metadata_json = file.read()
            
            return self.metadata_manager.deserialize_metadata(metadata_json)
        
        except Exception as e:
            print(f"Error importing metadata: {e}")
            return None
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file."""
        try:
            if not os.path.exists(file_path):
                return {"exists": False}
            
            stat = os.stat(file_path)
            
            info = {
                "exists": True,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_lakra": self.is_lakra_file(file_path),
                "has_metadata": False
            }
            
            # Check for metadata
            if info["is_lakra"]:
                try:
                    _, metadata = self.load_file(file_path)
                    info["has_metadata"] = metadata is not None
                except:
                    pass
            
            return info
        
        except Exception as e:
            print(f"Error getting file info: {e}")
            return {"exists": False, "error": str(e)}
    
    def backup_file(self, file_path: str) -> str:
        """Create a backup of a file."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Generate backup filename
            backup_path = file_path + ".backup"
            counter = 1
            
            while os.path.exists(backup_path):
                backup_path = f"{file_path}.backup.{counter}"
                counter += 1
            
            # Copy file
            with open(file_path, 'rb') as src:
                with open(backup_path, 'wb') as dst:
                    dst.write(src.read())
            
            return backup_path
        
        except Exception as e:
            raise Exception(f"Failed to backup file: {str(e)}")
