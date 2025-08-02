from machine import Pin
import time

class GateWeldingDetector():
    def __init__(self, gate_pin, welding_machine_pin):
        # Initialize pins for electrical signals
        self.gate = Pin(gate_pin, Pin.IN, Pin.PULL_DOWN)
        self.welding_machine = Pin(welding_machine_pin, Pin.IN, Pin.PULL_DOWN)
        
        # System status
        self.status = "ONLINE"
        self.last_state = "IDLE"
        self.state = self.last_state
        self.welding_completed = False  # Added missing attribute
        
        # Production tracking
        self.total_production = 0
        self.loaded_cylinder = 0
        self.non_welded_cylinders = 0
        
        # Gate state tracking
        self.gate_is_open = False
        self.gate_signal_count = 0
        
        # Welding time configuration (seconds per cylinder size)
        self.welding_times = {
            'small': 8,    # 8 seconds for small cylinders
            'medium': 12,  # 12 seconds for medium cylinders
            'large': 18    # 18 seconds for large cylinders
        }
        
        # Welding session tracking
        self.welding_started = False
        self.current_welding_start = 0
        self.saved_welding_times = []  # List of completed welding sessions
        self.current_session_time = 0
        self.welding_was_active = False  # Track if welding was active when gate opened
        
        # Adjustable margin of error for size determination (seconds)
        self.size_determination_margin = 1.0  # ±1 second as specified
        
    def state_update(self, status):
        """Update system state from external status string"""
        separator = status.split(" ")
        self.total_production = int(separator[1])
        self.loaded_cylinder = int(separator[2])
        self.last_state = separator[0]
        self.state = self.last_state
        self.welding_completed = separator[3] == "True"
        
    def determine_cylinder_size_and_count(self, total_welding_time):
        """Determine cylinder size and count based on total welding time"""
        # Find the closest matching size based on welding time
        closest_size = None
        min_difference = float('inf')
        
        for size, required_time in self.welding_times.items():
            difference = abs(total_welding_time - required_time)
            if difference < min_difference:
                min_difference = difference
                closest_size = size
        
        # Only accept if within the margin of error (1 second)
        if min_difference <= self.size_determination_margin:
            # Calculate how many cylinders based on total time
            cylinder_count = int(total_welding_time / self.welding_times[closest_size])
            return closest_size, cylinder_count
        else:
            return None, 0  # Size cannot be determined reliably
        
    def set_size_determination_margin(self, margin):
        """Set the margin of error for cylinder size determination (in seconds)"""
        self.size_determination_margin = margin
        print(f"Size determination margin set to: ±{margin} seconds")
        
    def detect_gate_and_welding_signals(self, publisher):
        """Main detection logic for gate signals and welding machine signals"""
        if self.state != self.last_state:
            print(f"State changed: {self.last_state} -> {self.state}")
            self.last_state = self.state
            publisher.publish_last_state(self.last_state, self.total_production, self.loaded_cylinder, self.welding_completed)
        
        # Get current signal states
        gate_signal = self.gate.value()  # 1 = gate open, 0 = gate closed
        welding_signal = self.welding_machine.value()  # 1 = welding active, 0 = welding inactive
        current_time = time.time()
        
        # Detect gate state changes
        if gate_signal != self.gate_is_open:
            # Gate state has changed
            if gate_signal:
                # Gate is now OPEN (value = 1)
                self.gate_is_open = True
                self.gate_signal_count += 1
                print(f"Gate signal #{self.gate_signal_count} - Gate OPENED")
                
                # Check if this is the first gate opening (assume cylinders were loaded)
                if self.gate_signal_count == 1:
                    print("First gate opening - assuming cylinders were loaded")
                    # Don't assume number, just note that cylinders were loaded
                
                # Check if this is gate opening after welding completed (welding pin = 0)
                elif self.welding_was_active and not welding_signal:
                    print("Gate opened after welding completed - calculating total welding time")
                    
                    # Add current session time if welding was active
                    if self.current_session_time > 0:
                        self.saved_welding_times.append(self.current_session_time)
                        print(f"Added current session: {self.current_session_time:.1f}s")
                    
                    # Calculate total welding time
                    total_welding_time = sum(self.saved_welding_times)
                    print(f"Total welding time: {total_welding_time:.1f}s")
                    
                    # Determine cylinder size and count
                    determined_size, cylinder_count = self.determine_cylinder_size_and_count(total_welding_time)
                    
                    if determined_size and cylinder_count > 0:
                        print(f"Determined: {cylinder_count} {determined_size} cylinders (±{self.size_determination_margin}s margin)")
                        
                        # Update production
                        self.total_production += cylinder_count
                        self.loaded_cylinder -= cylinder_count
                        
                        print(f"Production updated: +{cylinder_count} cylinders. Total production: {self.total_production}")
                        
                        # Publish production count
                        for i in range(cylinder_count):
                            publisher.publish_counter("+1")
                        
                    else:
                        print(f"Could not determine cylinder size/count from {total_welding_time:.1f}s welding time")
                        self.non_welded_cylinders += 1
                    
                    # Reset for next welding process
                    self.saved_welding_times.clear()
                    self.current_session_time = 0
                    self.welding_started = False
                    self.welding_was_active = False
                    print("Reset variables for next welding process")
                
            else:
                # Gate is now CLOSED (value = 0)
                self.gate_is_open = False
                print(f"Gate signal #{self.gate_signal_count} - Gate CLOSED")
        
        # Monitor welding machine signal
        if welding_signal and not self.welding_started:
            # Welding has started (pin = 1)
            print("Welding machine signal detected - welding started")
            self.welding_started = True
            self.welding_was_active = True
            self.current_welding_start = current_time
            self.current_session_time = 0
        
        elif self.welding_started:
            if welding_signal:
                # Welding is ongoing - update current session time
                self.current_session_time = current_time - self.current_welding_start
                self.welding_was_active = True
                print(f"Welding in progress: {self.current_session_time:.1f}s")
            else:
                # Welding stopped but gate didn't open - welding interrupted
                if self.current_session_time > 0:
                    self.saved_welding_times.append(self.current_session_time)
                    print(f"Welding interrupted. Saved session: {self.current_session_time:.1f}s")
                    print(f"Total saved time so far: {sum(self.saved_welding_times):.1f}s")
                    
                    # Reset for next session
                    self.current_session_time = 0
                    self.welding_started = False
                    self.welding_was_active = False
        
        # Update overall system state
        if not self.welding_started and len(self.saved_welding_times) == 0:
            self.state = "IDLE"
        elif self.welding_started and welding_signal:
            self.state = "WELDING_IN_PROGRESS"
        else:
            self.state = "CYLINDERS_LOADED"
    
    def set_cylinder_size(self, size):
        """Set the current cylinder size for welding time calculations"""
        if size in self.welding_times:
            print(f"Default cylinder size set to: {size} ({self.welding_times[size]}s per cylinder)")
        else:
            print(f"Invalid cylinder size: {size}. Available sizes: {list(self.welding_times.keys())}")
    
    def sensor_detect(self, publisher):
        """Main detection method called by external system"""
        self.detect_gate_and_welding_signals(publisher)
        
        # Publish current state if it changed
        if self.state != self.last_state:
            publisher.publish_last_state(self.state, self.total_production, self.loaded_cylinder, self.welding_completed) 