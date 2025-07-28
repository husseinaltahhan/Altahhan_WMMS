from machine import Pin
import time
class SensorDetections():
    def __init__(self, entrance_pin, exit_pin, weld_pin):
        self.entrance = Pin(entrance_pin, Pin.IN, Pin.PULL_DOWN)
        self.exit = Pin(exit_pin, Pin.IN, Pin.PULL_DOWN)
        self.weld = Pin(weld_pin, Pin.IN, Pin.PULL_DOWN)
        
        self.status = "ONLINE"
        self.last_state = "IDLE"
        self.welded = False

        self.non_welded_cylinders = 0
        self.timer = 0
        
        self.total_production = 0
        self.loaded_cylinder = 0
        
        
    def state_update(self, status):
        print ("hi")
        seperator = status.split(" ")
        self.total_production = int(seperator[1])
        self.loaded_cylinder = int(seperator[2])
        self.last_state = seperator[0]

        
    def detect_entry_exit(self, publisher):
        if self.last_state == "WELDING":
            return
        
        a = self.entrance.value()
        b = self.exit.value()
        state = self.last_state
        #print (state, a, b)
        # IDLE, A_TRIGGERED, B_TRIGGERED, A_B_TRIGGERED, B_A_TRIGGERED, B_ONLY, A_ONLY
        if state == "IDLE":
            if a and not b:
                state = "A_TRIGGERED"
            elif b and not a:
                state = "B_TRIGGERED"

        elif state == "A_TRIGGERED":
            if a and b:
                state = "AB_TRIGGERED"
            elif not a and not b:
                state = "IDLE"

        elif state == "B_TRIGGERED":
            if a and b:
                state = "BA_TRIGGERED"
            elif not a and not b:
                state = "IDLE"

        elif state == "AB_TRIGGERED":
            if not a and b:
                state = "B_ONLY"
            elif not a and not b: 
                state = "IDLE"

        elif state == "BA_TRIGGERED":
            if not b and a:
                state = "A_ONLY"
            elif not a and not b:
                state = "IDLE"

        elif state == "B_ONLY":
            if not b and not a:
                print ("entry detected") #ENTRY DETECTION
                self.loaded_cylinder += 1
                state = "IDLE"
            elif b and a:
                state = "AB_TRIGGERED"

        elif state == "A_ONLY":
            if not b and not a:
                print ("exit detected") #EXIT DETECTION
                self.loaded_cylinder -= 1
                if self.welded:
                    self.total_production += 1
                    publisher.publish_count("+1")
                else:
                    self.non_welded_cylinders += 1
                state = "IDLE"
                
            elif b and a:
                state = "BA_TRIGGERED"
                
        if state != self.last_state:
            print("im getting abused", state, self.last_state)
            self.last_state = state
            print("i wonder if i changed", state, self.last_state)
            publisher.publish_last_state(self.last_state, self.total_production, self.loaded_cylinder)
            
    
    def sensor_detect(self, publisher):
        self.detect_entry_exit(publisher)
        
        #Detecting welding
        if self.loaded_cylinder > 0:
            print(self.weld.value())
            if self.weld.value():
                print (self.last_state)
                if self.last_state != "WELDING":
                    self.last_state = "WELDING"
                    self.timer = time.time()
                    self.welded = False
                    publisher.publish_last_state(self.last_state, self.total_production, self.loaded_cylinder)
                    
                if (time.time() - self.timer) >= 10:
                    self.welded = True
            elif self.last_state == "WELDING":
                self.last_state = "IDLE"

