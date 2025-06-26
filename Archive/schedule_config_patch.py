
# Add this code to coordination_service.py in the _setup_routes method
# Place it right after the existing /schedule/status route

        @self.app.route('/schedule/config', methods=['GET', 'POST'])
        def schedule_config():
            """Get or set trading schedule configuration"""
            if request.method == 'GET':
                # Return current schedule configuration
                try:
                    # Get config from scheduler state or file
                    config = {
                        "enabled": self.scheduler_enabled,
                        "interval_minutes": self.schedule_interval,
                        "market_hours_only": getattr(self, 'market_hours_only', True),
                        "start_time": getattr(self, 'market_start', '09:30'),
                        "end_time": getattr(self, 'market_end', '16:00'),
                        "timezone": getattr(self, 'timezone', 'America/New_York'),
                        "excluded_days": getattr(self, 'excluded_days', ['Saturday', 'Sunday'])
                    }
                    return jsonify(config)
                except Exception as e:
                    self.logger.error(f"Error getting schedule config: {e}")
                    return jsonify({
                        "enabled": False,
                        "interval_minutes": 30,
                        "market_hours_only": True,
                        "start_time": "09:30",
                        "end_time": "16:00"
                    })
            
            else:  # POST - Update configuration
                try:
                    config = request.json
                    
                    # Update scheduler configuration
                    self.scheduler_enabled = config.get('enabled', False)
                    self.schedule_interval = config.get('interval_minutes', 30)
                    self.market_hours_only = config.get('market_hours_only', True)
                    self.market_start = config.get('start_time', '09:30')
                    self.market_end = config.get('end_time', '16:00')
                    
                    # Save configuration to file for persistence
                    config_file = './schedule_config.json'
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    # If scheduler is being enabled, start it
                    if self.scheduler_enabled:
                        if hasattr(self, '_start_scheduler'):
                            self._start_scheduler()
                        else:
                            # If no _start_scheduler method, just log
                            self.logger.info("Schedule enabled - scheduler will start on next check")
                    else:
                        # If scheduler is being disabled
                        if hasattr(self, '_stop_scheduler'):
                            self._stop_scheduler()
                        else:
                            self.logger.info("Schedule disabled")
                    
                    self.logger.info(f"Schedule configuration updated: {config}")
                    
                    return jsonify({
                        "status": "success",
                        "message": "Schedule configuration updated",
                        "config": config
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error updating schedule config: {e}")
                    return jsonify({"error": str(e)}), 500

# Also add this initialization code to the __init__ method of CoordinationService:
# (Add after self.logger is initialized)

        # Load schedule configuration
        self._load_schedule_config()

# And add this helper method to the class:

    def _load_schedule_config(self):
        """Load schedule configuration from file"""
        config_file = './schedule_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.scheduler_enabled = config.get('enabled', False)
                    self.schedule_interval = config.get('interval_minutes', 30)
                    self.market_hours_only = config.get('market_hours_only', True)
                    self.market_start = config.get('start_time', '09:30')
                    self.market_end = config.get('end_time', '16:00')
                    self.logger.info(f"Loaded schedule config: {config}")
            except Exception as e:
                self.logger.error(f"Error loading schedule config: {e}")
                self._set_default_schedule_config()
        else:
            self._set_default_schedule_config()
    
    def _set_default_schedule_config(self):
        """Set default schedule configuration"""
        self.scheduler_enabled = False
        self.schedule_interval = 30
        self.market_hours_only = True
        self.market_start = '09:30'
        self.market_end = '16:00'
