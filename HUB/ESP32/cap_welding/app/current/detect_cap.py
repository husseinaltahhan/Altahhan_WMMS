from machine import Pin
import time

class CapWeldingDetector():
    def __init__ (self, LW_pin, RW_pin, size_pins: dict = None, cylinder_pin=None):
        
        self.left_welder = Pin(LW_pin, Pin.IN, Pin.PULL_UP)
        self.right_welder = Pin(RW_pin, Pin.IN, Pin.PULL_UP)
        if cylinder_pin is not None: self.cylinder_pin = Pin(cylinder_pin, Pin.IN, Pin.PULL_UP)
        
        self.msw_pins={}
        
        #size_pins = {'120':20, '150': 24} size : pin_number
        if size_pins != None:
            for key, value in size_pins.items():
                self.msw_pins[key] = Pin(value, Pin.IN, Pin.PULL_UP)
        
        #sizes = ['120', '150', '180',...]        
        self.left_welding_time = 0.0
        self.right_welding_time = 0.0
        self.added_welding_time = 0.0
        
        self.total_time_needed = 60.0
        
        self.left_is_welding = False
        self.right_is_welding = False
        
        self.left_session_timer = 0.0
        self.right_session_timer = 0.0
        
        self.lastmsw_triggered = ""
        self.cylinder_size = ""
    
    def determine_size(self):
        if self.lastmsw_triggered != "":
            self.cylinder_size = self.lastmsw_triggered
    
    def debounced_read(self, pin: Pin, stable_count=3, delay_ms=5) -> int:
        """Return 0/1 after `stable_count` identical samples spaced by `delay_ms`."""
        last = pin.value()
        count = 1
        while count < stable_count:
            time.sleep_ms(delay_ms)
            v = pin.value()
            if v == last:
                count += 1
            else:
                last = v
                count = 1
        return last
    
    def detection(self, publisher):
        
        present = (self.debounced_read(self.cylinder_pin, 3, 8) == 0)
        
         
        if present:
            
            left_welder = (self.debounced_read(self.left_welder, 3, 8) == 0)
            right_welder = (self.debounced_read(self.right_welder, 3, 8) == 0)
            
            current_time = time.tick_ms()
            
            if left_welder and not self.left_is_welding:
                self.left_is_welding = True
                self.left_session_timer = current_time
            elif not left_welder and self.left_is_welding:
                self.left_is_welding = False
                self.left_welding_time += (time.ticks_diff(current_time, self.left_session_timer) / 1000.0)
                self.added_welding_time += (time.ticks_diff(current_time, self.left_session_timer) / 1000.0)
            
            if right_welder and not self.right_is_welding:
                self.right_is_welding = True
                self.right_session_timer = current_time
            elif not right_welder and self.right_is_welding:
                self.right_is_welding = False
                self.right_welding_time += (time.ticks_diff(current_time, self.right_session_timer) / 1000.0)
                self.added_welding_time += (time.ticks_diff(current_time, self.right_session_timer) / 1000.0)
            

            if self.left_is_welding or self.right_is_welding:
                for key, value in self.msw_pins.items():
                    pin_val = (self.debounced_read(value, 3, 8) ==0)
                    if pin_val:
                        self.lastmsw_triggered = key
            
            
        else:
            if present == None:
                publisher.publish_error("Cylinder detection sensor not wired")
                return 
            if self.added_welding_time >= self.total_time_needed:
                self.determine_size()
                publisher.publish_counter("+1", self.cylinder_size)
                
            self.lastmsw_triggered = ""
            self.cylinder_size = ""
            
            self.left_is_welding = False
            self.right_is_welding = False
            
            self.left_welding_time = 0.0
            self.right_welding_time = 0.0
            self.added_welding_time = 0.0
            
            self.left_session_timer = 0.0
            self.right_session_timer = 0.0
                            
    
    def main(self, publisher):
        try:
            self.detection(publisher)
        except Exception as e:
            publisher.publish_error("Error in Cap Detection: %r" %e)