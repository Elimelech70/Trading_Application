
# Add this to coordination_service.py to fix the sync issue
# Replace or update the /schedule/status endpoint handler

@self.app.route('/schedule/status', methods=['GET'])
def get_schedule_status():
    """Get trading schedule status - synchronized with config"""
    # Read from the same config file as /schedule/config
    config_file = './schedule_config.json'
    
    try:
        # Load config from file
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            # Use defaults
            config = {
                "enabled": False,
                "interval_minutes": 30,
                "market_hours_only": True,
                "start_time": "09:30",
                "end_time": "16:00",
                "timezone": "America/New_York",
                "excluded_days": ["Saturday", "Sunday"]
            }
        
        # Add runtime information
        config['last_run'] = getattr(self, '_last_scheduled_run', None)
        
        # Calculate next run if enabled
        if config['enabled']:
            from datetime import datetime, timedelta
            now = datetime.now()
            if hasattr(self, '_last_scheduled_run') and self._last_scheduled_run:
                next_run = self._last_scheduled_run + timedelta(minutes=config['interval_minutes'])
                config['next_run'] = next_run.strftime('%Y-%m-%d %H:%M:%S')
            else:
                config['next_run'] = f"In {config['interval_minutes']} minutes"
        else:
            config['next_run'] = None
        
        return jsonify(config)
        
    except Exception as e:
        self.logger.error(f"Error getting schedule status: {e}")
        return jsonify({
            "enabled": False,
            "message": "Error reading schedule configuration",
            "error": str(e)
        })
