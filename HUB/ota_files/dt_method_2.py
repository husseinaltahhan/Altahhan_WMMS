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
        
        # Production tracking
        self.total_production = 0
        self.loaded_cylinder = 0
        self.non_welded_cylinders = 0
        
        # Gate state tracking
        self.gate_is_open = False
        self.last_gate_signal_time = 0
        self.gate_signal_count = 0
        
        # Welding machine state
        self.welding_started = False
        self.welding_completed = False
        self.welding_start_time = 0
        self.total_welding_time = 0
        
        # Welding time configuration (seconds per cylinder size)
        self.welding_times = {
            'small': 8,    # 8 seconds for small cylinders
            'medium': 12,  # 12 seconds for medium cylinders
            'large': 18    # 18 seconds for large cylinders
        }
        self.current_cylinder_size = 'medium'  # Default size
        
        # Cylinder tracking based on welding time
        self.cylinders_in_machine = []  # List of cylinder objects
        self.cylinder_id_counter = 0    # Unique ID for each cylinder
        self.expected_cylinders = 0     # Expected number based on welding time
        
        # Timing for welding detection
        self.minimum_welding_time = 5   # Minimum time to consider as welding
        self.gate_debounce_time = 0.5   # seconds
        
    def state_update(self, status):
        """Update system state from external status string"""
        separator = status.split(" ")
        self.total_production = int(separator[1])
        self.loaded_cylinder = int(separator[2])
        self.last_state = separator[0]
        self.state = self.last_state
        self.welding_completed = separator[3] == "True"
        
    def create_cylinder(self, size='medium'):
        """Create a new cylinder object with unique ID and size"""
        self.cylinder_id_counter += 1
        return {
            'id': self.cylinder_id_counter,
            'size': size,
            'state': 'ENTERED',
            'welding_started': False,
            'welding_completed': False,
            'welding_timer': 0,
            'entry_time': time.time()
        }
        
    def calculate_expected_cylinders(self, welding_duration):
        """Calculate expected number of cylinders based on welding time"""
        time_per_cylinder = self.welding_times[self.current_cylinder_size]
        expected = int(welding_duration / time_per_cylinder)
        return max(1, expected)  # At least 1 cylinder
        
    def detect_gate_and_welding_signals(self, publisher):
        """Main detection logic for gate signals and welding machine signals"""
        if self.state != self.last_state:
            print(f"State changed: {self.last_state} -> {self.state}")
            self.last_state = self.state
            publisher.publish_last_state(self.last_state, self.total_production, self.loaded_cylinder, self.welding_completed)
        
        # Get current signal states
        gate_signal = self.gate.value()
        welding_signal = self.welding_machine.value()
        current_time = time.time()
        
        # Detect gate signal transitions (rising edge with debounce)
        if gate_signal and (current_time - self.last_gate_signal_time) > self.gate_debounce_time:
            self.gate_signal_count += 1
            self.last_gate_signal_time = current_time
            
            # Determine if gate is opening or closing based on signal count
            if self.gate_signal_count % 2 == 1:  # Odd count = gate opening
                self.gate_is_open = True
                print(f"Gate signal #{self.gate_signal_count} - Gate OPENING")
            else:  # Even count = gate closing
                self.gate_is_open = False
                print(f"Gate signal #{self.gate_signal_count} - Gate CLOSING")
                
                # When gate closes, create expected number of cylinders based on previous welding time
                if len(self.cylinders_in_machine) == 0 and self.total_welding_time > 0:
                    self.expected_cylinders = self.calculate_expected_cylinders(self.total_welding_time)
                    print(f"Creating {self.expected_cylinders} cylinders based on welding time: {self.total_welding_time}s")
                    
                    for i in range(self.expected_cylinders):
                        new_cylinder = self.create_cylinder(self.current_cylinder_size)
                        self.cylinders_in_machine.append(new_cylinder)
                        self.loaded_cylinder += 1
                        print(f"New cylinder {new_cylinder['id']} ({new_cylinder['size']}) created. Total cylinders: {len(self.cylinders_in_machine)}")
        
        # Update welding machine state
        if welding_signal and not self.welding_started:
            print("Welding machine signal detected - welding started")
            self.welding_started = True
            self.welding_start_time = current_time
            # Mark all cylinders in machine as welding started
            for cylinder in self.cylinders_in_machine:
                if cylinder['state'] == 'ENTERED':
                    cylinder['welding_started'] = True
                    cylinder['welding_timer'] = current_time
                    cylinder['state'] = 'WELDING_IN_PROGRESS'
        
        # Monitor welding process for all cylinders
        if self.welding_started:
            self.total_welding_time = current_time - self.welding_start_time
            
            for cylinder in self.cylinders_in_machine:
                if cylinder['state'] == 'WELDING_IN_PROGRESS':
                    if welding_signal:
                        # Check if minimum welding time has passed for this cylinder size
                        cylinder_welding_time = current_time - cylinder['welding_timer']
                        required_time = self.welding_times[cylinder['size']]
                        
                        if cylinder_welding_time >= required_time:
                            cylinder['welding_completed'] = True
                            cylinder['state'] = 'WELDING_COMPLETED'
                            print(f"Cylinder {cylinder['id']} ({cylinder['size']}) welding completed after {cylinder_welding_time:.1f}s")
                    else:
                        # Welding stopped prematurely
                        cylinder['welding_completed'] = False
                        cylinder['state'] = 'WELDING_INTERRUPTED'
                        print(f"Cylinder {cylinder['id']} ({cylinder['size']}) welding interrupted")
        
        # Process completed cylinders (exit detection based on gate signals)
        completed_cylinders = []
        for cylinder in self.cylinders_in_machine:
            if cylinder['state'] in ['WELDING_COMPLETED', 'WELDING_INTERRUPTED']:
                # Check if gate has opened and closed again (indicating exit)
                # We need at least 2 more gate signals after cylinder entry
                if self.gate_signal_count >= 2:  # Gate has opened and closed at least once
                    completed_cylinders.append(cylinder)
                    self.loaded_cylinder -= 1
                    
                    if cylinder['welding_completed']:
                        self.total_production += 1
                        print(f"Cylinder {cylinder['id']} ({cylinder['size']}) - Full welded cylinder completed! Total production: {self.total_production}")
                        publisher.publish_counter("+1")
                    else:
                        self.non_welded_cylinders += 1
                        print(f"Cylinder {cylinder['id']} ({cylinder['size']}) - Non-welded cylinder detected. Count: {self.non_welded_cylinders}")
        
        # Remove completed cylinders from tracking
        for cylinder in completed_cylinders:
            self.cylinders_in_machine.remove(cylinder)
            print(f"Cylinder {cylinder['id']} removed from tracking. Remaining: {len(self.cylinders_in_machine)}")
        
        # Update overall system state
        if len(self.cylinders_in_machine) == 0:
            self.state = "IDLE"
            self.welding_started = False
            self.welding_completed = False
            self.total_welding_time = 0
        elif any(cylinder['state'] == 'WELDING_IN_PROGRESS' for cylinder in self.cylinders_in_machine):
            self.state = "WELDING_IN_PROGRESS"
        elif any(cylinder['state'] == 'WELDING_COMPLETED' for cylinder in self.cylinders_in_machine):
            self.state = "WELDING_COMPLETED"
        else:
            self.state = "CYLINDERS_LOADED"
    
    def set_cylinder_size(self, size):
        """Set the current cylinder size for welding time calculations"""
        if size in self.welding_times:
            self.current_cylinder_size = size
            print(f"Cylinder size set to: {size} ({self.welding_times[size]}s per cylinder)")
        else:
            print(f"Invalid cylinder size: {size}. Available sizes: {list(self.welding_times.keys())}")
    
    def sensor_detect(self, publisher):
        """Main detection method called by external system"""
        self.detect_gate_and_welding_signals(publisher)
        
        # Publish current state if it changed
        if self.state != self.last_state:
            publisher.publish_last_state(self.state, self.total_production, self.loaded_cylinder, self.welding_completed) 