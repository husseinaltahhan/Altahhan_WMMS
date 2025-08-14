from machine import Pin
import time
import math

class GateWeldingDetector():
    def __init__(self, gate_pin, welding_machine_pin):
        # Initialize pins for electrical signals
        self.gate = Pin(gate_pin, Pin.IN, Pin.PULL_UP)
        self.welding_machine = Pin(welding_machine_pin, Pin.IN, Pin.PULL_UP)
        
        # System status
        self.status = "ONLINE"
        self.last_state = "IDLE"
        self.state = self.last_state
        self.welding_completed = False  # Added missing attribute
        
        # Production tracking
        self.total_production = 0
        self.non_welded_cylinders = 0
        
        # Gate state tracking
        self.gate_is_open = False
        self.gate_signal_count = 0
        
        # Welding time configuration (seconds per cylinder size)
        self.welding_times = {
            '120': 151,    # 8 seconds for small cylinders
            '150': 189  # 12 seconds for medium cylinders
        }
        
        # Welding session tracking
        self.welding_started = False
        self.current_welding_start = 0.0
        self.saved_welding_times = []  # List of completed welding sessions
        self.current_session_time = 0
        self.welding_was_active = False  # Track if welding was active when gate opened
        
        # Adjustable margin of error for size determination (seconds)
        self.size_determination_margin = 1.0  # ±1 second as specified
        
    def state_update(self, status):
        """Update system state from external status string"""
        separator = status.split(" ")
        self.total_production = int(separator[1])
        self.last_state = str(separator[0])
        self.state = self.last_state
        
        
    
    def determine_cylinder_size_and_count(self, total_welding_time):
        """Determine cylinder size and count based on total welding time"""
        # Find the closest matching size based on welding time
        closest_size = None
        min_difference = 0.11
        
        for size, required_time in self.welding_times.items():
            multiple = total_welding_time/required_time
            if abs(multiple - round(multiple)) <= min_difference:
                closest_size = size
        
        # Only accept if within the margin of error (1 second)
        if closest_size:
            # Calcu+late how many cylinders based on total time
            cylinder_count = int(round(total_welding_time / self.welding_times[closest_size]))
            return closest_size, cylinder_count
        else:
            return None, 0  # Size cannot be determined reliably
     
     
     
    def set_size_determination_margin(self, margin):
        """Set the margin of error for cylinder size determination (in seconds)"""
        self.size_determination_margin = margin
        print(f"Size determination margin set to: ±{margin} seconds")
        
        
        
    def stable_read(self, samples=5, delay_ms=5):
        v = None
        for _ in range(samples):
            nv = self.gate.value()
            if v is None: v = nv
            elif nv != v: return None  # unstable
            time.sleep_ms(delay_ms)
        return v
        
        
        
    def detect_gate_and_welding_signals(self, publisher):
        """Main detection logic for gate signals and welding machine signals"""
        if self.state != self.last_state:
            print(f"State changed: {self.last_state} -> {self.state}")
            self.last_state = self.state
            publisher.publish_last_state(self.last_state, self.total_production, f"{sum(self.saved_welding_times)}")
        
        # Get current signal states
        raw_gate = self.stable_read()
        if raw_gate is not None:
            gate_signal = self.gate.value()  # 1 = gate open, 0 = gate closed
        else:
            gate_signal = 0
        welding_signal = self.welding_machine.value()  # 1 = welding active, 0 = welding inactive
        current_time = time.time()
        
        # Detect gate state changes
        if not gate_signal != self.gate_is_open:
            # Gate state has changed
            if not gate_signal:
                # Gate is now OPEN (value = 1)
                self.gate_is_open = True
                self.gate_signal_count += 1
                print(f"Gate signal #{self.gate_signal_count} - Gate OPENED")
                publisher.publish_log(f"Gate signal #{self.gate_signal_count} - Gate OPENED")
                print (self.welding_was_active, welding_signal)
                # Check if this is gate opening after welding completed (welding pin = 0)
                if self.welding_was_active and welding_signal:
                    print("Gate opened after welding completed - calculating total welding time")
                    publisher.publish_log("Gate opened after welding completed - calculating total welding time")
                    
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
                        
                        print(f"Production updated: +{cylinder_count} cylinders. Total production: {self.total_production}")
                        
                        # Publish production count
                        #for i in range(cylinder_count):
                            #publisher.publish_counter("+1")
                        publisher.publish_counter(f"+{cylinder_count}", determined_size)
                    else:
                        print(f"Could not determine cylinder size/count from {total_welding_time:.1f}s welding time")
                        self.non_welded_cylinders += 1
                    
                    # Reset for next welding process
                    self.saved_welding_times.clear()
                    total_welding_time = 0.0
                    self.current_session_time = 0.0
                    self.welding_started = False
                    self.welding_was_active = False
                    print("Reset variables for next welding process")
                
            else:
                # Gate is now CLOSED (value = 0)
                self.gate_is_open = False
                print(f"Gate signal #{self.gate_signal_count} - Gate CLOSED")
                
        
        # Monitor welding machine signal
        if not welding_signal and not self.welding_started:
            start_time = time.ticks_ms()
            
            while time.ticks_diff(time.ticks_ms(), start_time) < 500:
                if self.welding_started:
                    break
                
            else:
                # Welding has started (pin = 1)
                print("Welding machine signal detected - welding started")
                self.welding_started = True
                self.welding_was_active = True
                self.current_welding_start = current_time
                self.current_session_time = 0.0
        
        elif self.welding_started:
                if not welding_signal:
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
        elif self.welding_started and not welding_signal:
            self.state = "WELDING_IN_PROGRESS"
        else:
            self.state = "CYLINDERS_LOADED"
       
    
    def sensor_detect(self, publisher):
        """Main detection method called by external system"""
        try:
            self.detect_gate_and_welding_signals(publisher)
        except Exception as e:
            print (f"Error in Detections: {e}")
            publisher.publish_error(e)
        
        if self.state != self.last_state:
            print(f"State changed: {self.last_state} -> {self.state}")
            self.last_state = self.state
            publisher.publish_last_state(self.last_state, self.total_production, f"{sum(self.saved_welding_times)}")
