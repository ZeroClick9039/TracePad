"""
Metadata Manager - Handles metadata serialization and deserialization.
"""

import json
import time
from typing import Dict, Any, Optional


class MetadataManager:
    """Manages metadata serialization and validation."""

    def __init__(self):
        self.version = "1.0"

    def serialize_metadata(self, metadata: Dict[str, Any]) -> str:
        """Serialize metadata to compact JSON string."""
        try:
            serialized = {
                'ghostkey_metadata': {
                    'version': self.version,
                    'created': time.time(),
                    'data': metadata
                }
            }

            # Compact JSON with no indentation or extra spaces
            return json.dumps(serialized, separators=(',', ':'), ensure_ascii=False)

        except Exception as e:
            raise Exception(f"Failed to serialize metadata: {str(e)}")

    def deserialize_metadata(self, metadata_str: str) -> Optional[Dict[str, Any]]:
        """Deserialize metadata from JSON string."""
        try:
            if not metadata_str.strip():
                return None

            data = json.loads(metadata_str)

            if 'ghostkey_metadata' in data:
                return data['ghostkey_metadata']['data']
            else:
                if 'ranges' in data:
                    return data

            return None

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"Error deserializing metadata: {e}")
            return None

    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Validate metadata structure."""
        try:
            if not isinstance(metadata, dict):
                return False

            if 'ranges' not in metadata:
                return False

            ranges = metadata['ranges']
            if not isinstance(ranges, list):
                return False

            for range_info in ranges:
                if not isinstance(range_info, dict):
                    return False

                required_fields = ['start', 'end', 'source']
                for field in required_fields:
                    if field not in range_info:
                        return False

                if not isinstance(range_info['start'], int):
                    return False
                if not isinstance(range_info['end'], int):
                    return False
                if not isinstance(range_info['source'], str):
                    return False

                if range_info['start'] < 0 or range_info['end'] < 0:
                    return False
                if range_info['start'] >= range_info['end']:
                    return False

                if range_info['source'] not in ['manual', 'pasted']:
                    return False

            return True

        except Exception as e:
            print(f"Error validating metadata: {e}")
            return False

    def merge_metadata(self, metadata1: Dict[str, Any], metadata2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two metadata dictionaries."""
        try:
            merged = {
                'version': self.version,
                'ranges': []
            }

            all_ranges = []

            if metadata1 and 'ranges' in metadata1:
                all_ranges.extend(metadata1['ranges'])

            if metadata2 and 'ranges' in metadata2:
                all_ranges.extend(metadata2['ranges'])

            all_ranges.sort(key=lambda x: x.get('start', 0))

            merged_ranges = []

            for range_info in all_ranges:
                if (merged_ranges and
                    merged_ranges[-1]['source'] == range_info['source'] and
                    merged_ranges[-1]['end'] >= range_info['start']):
                    merged_ranges[-1]['end'] = max(merged_ranges[-1]['end'], range_info['end'])
                else:
                    merged_ranges.append(range_info.copy())

            merged['ranges'] = merged_ranges
            return merged

        except Exception as e:
            print(f"Error merging metadata: {e}")
            return {'version': self.version, 'ranges': []}

    def get_stats(self, metadata: Dict[str, Any], total_length: int) -> Dict[str, Any]:
        """Calculate statistics from metadata."""
        try:
            stats = {
                'total_chars': total_length,
                'typed_chars': 0,
                'pasted_chars': 0,
                'unknown_chars': 0,
                'typed_percentage': 0.0,
                'pasted_percentage': 0.0,
                'unknown_percentage': 0.0,
                'total_ranges': 0,
                'typed_ranges': 0,
                'pasted_ranges': 0
            }

            if not metadata or 'ranges' not in metadata:
                stats['unknown_chars'] = total_length
                stats['unknown_percentage'] = 100.0 if total_length > 0 else 0.0
                return stats

            ranges = metadata['ranges']
            stats['total_ranges'] = len(ranges)

            tracked_chars = 0

            for range_info in ranges:
                start = range_info.get('start', 0)
                end = range_info.get('end', 0)
                source = range_info.get('source', 'unknown')
                length = end - start

                tracked_chars += length

                if source == 'manual':
                    stats['typed_chars'] += length
                    stats['typed_ranges'] += 1
                elif source == 'pasted':
                    stats['pasted_chars'] += length
                    stats['pasted_ranges'] += 1

            stats['unknown_chars'] = max(0, total_length - tracked_chars)

            if total_length > 0:
                stats['typed_percentage'] = (stats['typed_chars'] / total_length) * 100
                stats['pasted_percentage'] = (stats['pasted_chars'] / total_length) * 100
                stats['unknown_percentage'] = (stats['unknown_chars'] / total_length) * 100

            return stats

        except Exception as e:
            print(f"Error calculating stats: {e}")
            return {
                'total_chars': total_length,
                'typed_chars': 0,
                'pasted_chars': 0,
                'unknown_chars': total_length,
                'typed_percentage': 0.0,
                'pasted_percentage': 0.0,
                'unknown_percentage': 100.0,
                'total_ranges': 0,
                'typed_ranges': 0,
                'pasted_ranges': 0
            }
