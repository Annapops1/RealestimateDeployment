import time
from datetime import datetime, timedelta
import threading

# Global flag to prevent multiple initializations
_thread_started = False

def update_recommendation_engine():
    """Background task to update recommendation engine daily"""
    global _thread_started
    
    # Only run once
    if _thread_started:
        return
    _thread_started = True
    
    # Import inside function to avoid circular imports
    from flask import current_app
    
    while True:
        try:
            # Import recommendation_engine here to avoid circular imports
            from app.utils.recommendation_engine import recommendation_engine
            
            # Update engine if it's never been updated or if it's been more than a day
            if not recommendation_engine.last_update or \
               (datetime.utcnow() - recommendation_engine.last_update) > timedelta(days=1):
                recommendation_engine.build_property_features()
                recommendation_engine.build_user_preferences()
                recommendation_engine.build_property_similarity_matrix()
                recommendation_engine.build_user_property_matrix()
                recommendation_engine.last_update = datetime.utcnow()
                print(f"Recommendation engine updated at {recommendation_engine.last_update}")
        except Exception as e:
            print(f"Error updating recommendation engine: {str(e)}")
        
        # Sleep for 6 hours before checking again
        time.sleep(6 * 60 * 60) 