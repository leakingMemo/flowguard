"""State persistence for FlowGuard."""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from .models import WorkflowInstance
from .exceptions import PersistenceError


class StateStore:
    """Handles persistence of workflow state."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize state store."""
        self.storage_dir = storage_dir or Path.home() / ".flowguard-state"
        self.storage_dir.mkdir(exist_ok=True)
        
    def _get_instance_path(self, instance_id: str) -> Path:
        """Get the file path for an instance."""
        return self.storage_dir / f"{instance_id}.json"
    
    def save(self, instance: WorkflowInstance) -> None:
        """Save a workflow instance to disk."""
        try:
            instance_path = self._get_instance_path(instance.id)
            
            # Convert to dict and handle datetime serialization
            data = instance.model_dump()
            data['created_at'] = instance.created_at.isoformat()
            data['updated_at'] = instance.updated_at.isoformat()
            
            with open(instance_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            raise PersistenceError(f"Failed to save instance: {e}")
    
    def load(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Load a workflow instance from disk."""
        try:
            instance_path = self._get_instance_path(instance_id)
            
            if not instance_path.exists():
                return None
                
            with open(instance_path, 'r') as f:
                data = json.load(f)
            
            # Convert ISO format strings back to datetime
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            return WorkflowInstance(**data)
            
        except Exception as e:
            raise PersistenceError(f"Failed to load instance: {e}")
    
    def delete(self, instance_id: str) -> bool:
        """Delete a workflow instance from disk."""
        try:
            instance_path = self._get_instance_path(instance_id)
            
            if instance_path.exists():
                instance_path.unlink()
                return True
            return False
            
        except Exception as e:
            raise PersistenceError(f"Failed to delete instance: {e}")
    
    def list_instances(self) -> List[Dict[str, str]]:
        """List all stored instances."""
        instances = []
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    instances.append({
                        "id": data["id"],
                        "workflow_name": data["workflow_name"],
                        "current_state": data["current_state"],
                        "updated_at": data["updated_at"]
                    })
            except Exception:
                # Skip corrupted files
                continue
                
        # Sort by updated time, most recent first
        instances.sort(key=lambda x: x["updated_at"], reverse=True)
        return instances
    
    def get_active_instance(self, workflow_name: str) -> Optional[WorkflowInstance]:
        """Get the most recently updated instance for a workflow."""
        instances = self.list_instances()
        
        for instance_info in instances:
            if instance_info["workflow_name"] == workflow_name:
                return self.load(instance_info["id"])
                
        return None
    
    def cleanup_old_instances(self, days: int = 30) -> int:
        """Remove instances older than specified days. Returns count of deleted instances."""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        deleted = 0
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    updated_at = datetime.fromisoformat(data["updated_at"])
                    
                if updated_at < cutoff:
                    file_path.unlink()
                    deleted += 1
                    
            except Exception:
                # Skip files we can't process
                continue
                
        return deleted