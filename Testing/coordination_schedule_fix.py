#!/usr/bin/env python3
"""
Fix for adding schedule endpoints to coordination service
Add this code to coordination_service.py in the _setup_routes method
"""

# Add these routes to coordination_service.py _setup_routes method:

@self.app.route('/schedule/status', methods=['GET'])
def get_schedule_status():
    """Proxy schedule status to scheduler service"""
    try:
        # Forward to scheduler service
        response = requests.get('http://localhost:5011/status', timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
    except Exception as e:
        self.logger.error(f"Error getting schedule status: {e}")
    
    return jsonify({
        "enabled": False,
        "message": "Scheduler service not available",
        "next_run": None
    })

@self.app.route('/schedule/config', methods=['GET', 'POST'])
def schedule_config():
    """Proxy schedule config to scheduler service"""
    if request.method == 'GET':
        try:
            response = requests.get('http://localhost:5011/config', timeout=5)
            if response.status_code == 200:
                return jsonify(response.json())
        except Exception as e:
            self.logger.error(f"Error getting schedule config: {e}")
        
        # Default config if scheduler not available
        return jsonify({
            "enabled": False,
            "interval_minutes": 30,
            "market_hours_only": True,
            "start_time": "09:30",
            "end_time": "16:00"
        })
    
    else:  # POST
        try:
            # Forward config to scheduler
            response = requests.post('http://localhost:5011/config', 
                                   json=request.json, timeout=5)
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({"error": "Failed to update scheduler config"}), 500
        except Exception as e:
            self.logger.error(f"Error updating schedule config: {e}")
            return jsonify({"error": str(e)}), 500
