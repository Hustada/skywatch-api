#!/usr/bin/env python3
"""
Store external API data with proper organization and metadata.
"""

import json
import os
from datetime import datetime
from pathlib import Path

class ExternalDataStorage:
    def __init__(self, base_data_dir: str = "data/external"):
        self.base_dir = Path(base_data_dir)
        self.metadata_dir = self.base_dir / "metadata"
    
    def store_batch(self, source: str, data: list, batch_number: int = None):
        """Store a batch of API data."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_suffix = f"_batch_{batch_number:03d}" if batch_number else ""
        filename = f"{source}_{timestamp}{batch_suffix}.json"
        
        # Store in raw directory
        raw_dir = self.base_dir / source / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        filepath = raw_dir / filename
        
        # Prepare data with metadata
        data_package = {
            "metadata": {
                "source": source,
                "fetch_timestamp": datetime.now().isoformat(),
                "batch_number": batch_number,
                "record_count": len(data),
                "api_key_used": "*** (hidden)",
                "schema_version": "1.0"
            },
            "data": data
        }
        
        # Write data
        with open(filepath, 'w') as f:
            json.dump(data_package, f, indent=2)
        
        print(f"✅ Stored {len(data)} records to {filepath}")
        self._update_source_metadata(source, len(data))
        
        return filepath
    
    def _update_source_metadata(self, source: str, record_count: int):
        """Update source metadata tracking."""
        
        metadata_file = self.metadata_dir / "sources.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {"sources": {}}
        
        if source not in metadata["sources"]:
            metadata["sources"][source] = {}
        
        metadata["sources"][source].update({
            "last_fetch": datetime.now().isoformat(),
            "total_records": metadata["sources"][source].get("total_records", 0) + record_count,
            "status": "active"
        })
        metadata["last_updated"] = datetime.now().isoformat()
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

# Example usage:
if __name__ == "__main__":
    # Example: Store sample MUFON data
    storage = ExternalDataStorage()
    
    sample_data = [
        {
            "id": "test_001",
            "date": "2024-01-15",
            "location": "Phoenix, AZ",
            "shape": "triangle",
            "description": "Large triangular craft with lights"
        }
    ]
    
    storage.store_batch("mufon", sample_data, batch_number=1)
    print("Sample storage complete!")
