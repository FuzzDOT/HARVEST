"""
Session storage for frontend prediction results.
Stores user prediction results temporarily for individual API access.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

class PredictionSession:
    """Manages temporary storage of prediction results for frontend access."""
    
    def __init__(self):
        self.sessions = {}
        self.session_expiry = timedelta(hours=1)  # Sessions expire after 1 hour
    
    def create_session(self, prediction_results: Dict[str, Any]) -> str:
        """
        Create a new session with prediction results.
        
        Returns:
            Session ID for accessing individual results
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'data': prediction_results,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + self.session_expiry
        }
        
        # Clean up expired sessions
        self._cleanup_expired_sessions()
        
        return session_id
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        if session_id not in self.sessions:
            return None
            
        session = self.sessions[session_id]
        
        # Check if session has expired
        if datetime.now() > session['expires_at']:
            del self.sessions[session_id]
            return None
            
        return session['data']
    
    def get_result_by_index(self, session_id: str, field_prefix: str, index: int) -> Any:
        """
        Get a specific result field by index from a session.
        
        Args:
            session_id: Session identifier
            field_prefix: Field prefix (e.g., 'cropName', 'cropPrice')
            index: Index (1-5)
            
        Returns:
            The specific field value or None if not found
        """
        session_data = self.get_session_data(session_id)
        if not session_data:
            return None
            
        field_name = f"{field_prefix}{index}"
        return session_data.get(field_name)
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time > session['expires_at']
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]


# Global session manager instance
session_manager = PredictionSession()