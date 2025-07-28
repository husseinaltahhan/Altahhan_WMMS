from machine import Pin
import time
class SensorDetections():
    def __init__(self, entrance_pin, exit_pin, weld_pin):
        self.entrance = Pin(entrance_pin, Pin.IN, Pin.PULL_DOWN)
        self.exit = Pin(exit_pin, Pin.IN, Pin.PULL_DOWN)
        self.weld = Pin(weld_pin, Pin.IN, Pin.PULL_DOWN)
        
        self.status = "ONLINE"
        self.last_state = "IDLE"
        self.state = self.last_state
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
        print(self.loaded_cylinder, self.loaded_cylinder == int)
        self.last_state = seperator[0]
        self.state = self.last_state
        self.welded = seperator[3]


        
    def detect_entry_exit(self, publisher):
        if self.state != self.last_state:
            print("im getting abused", self.state, self.last_state)
            self.last_state = self.state
            print("i wonder if i changed", self.state, self.last_state)
            publisher.publish_last_state(self.last_state, self.total_production, self.loaded_cylinder, self.welded)


        if self.last_state == "WELDING":
            return
        
        a = self.entrance.value()
        b = self.exit.value()
            
        self.state = self.last_state

        #print (state, a, b)
        # IDLE, A_TRIGGERED, B_TRIGGERED, A_B_TRIGGERED, B_A_TRIGGERED, B_ONLY, A_ONLY
        if self.state == "IDLE":
            if a and not b:
                self.state = "A_TRIGGERED"
            elif self.loaded_cylinder > 0: 
                if b and not a:
                    self.state = "B_TRIGGERED"

        elif self.state == "A_TRIGGERED":
            if a and b:
                self.state = "AB_TRIGGERED"
            elif not a and not b:
                self.state = "IDLE"

        elif self.state == "AB_TRIGGERED":
            if not a and b:
                self.state = "B_ONLY"
            elif not a and not b:
                print ("SURPRITSEEEEE")
                self.state = "IDLE"

        elif self.state == "B_ONLY":
            if not b and not a:
                print ("entry detected") #ENTRY DETECTION
                self.loaded_cylinder += 1
                self.state = "IDLE"
            elif b and a:
                self.state = "AB_TRIGGERED"
        
        if self.loaded_cylinder > 0:
            if self.state == "B_TRIGGERED":
                if a and b:
                    self.state = "BA_TRIGGERED"
                elif not a and not b:
                    self.state = "IDLE"
            
            elif self.state == "BA_TRIGGERED":
                if not b and a:
                    self.state = "A_ONLY"
                    print (self.state)
                elif not a and not b:
                    self.state = "IDLE"
                
            elif self.state == "A_ONLY":
                if not b and not a:
                    print ("exit detected") #EXIT DETECTION
                    self.loaded_cylinder -= 1
                    if self.welded:
                        self.total_production += 1
                        print(self.total_production)
                        publisher.publish_counter("+1")
                    else:
                        self.non_welded_cylinders += 1

                    self.state = "IDLE"
                    if self.loaded_cylinder == 0:
                        self.welded = False
                    
                elif b and a:
                    state = "BA_TRIGGERED"
            
    
    def sensor_detect(self, publisher):
        self.detect_entry_exit(publisher)
    
        
        #Detecting welding
        if self.loaded_cylinder > 0:
            if self.weld.value():
                if self.state != "WELDING":
                    print("WELDING")
                    self.state = "WELDING"
                    self.timer = time.time()
                    self.welded = False
                    publisher.publish_last_state(self.last_state, self.total_production, self.loaded_cylinder, self.welded)
                    
                if (time.time() - self.timer) >= 10:
                    self.welded = True
                    
            elif self.state == "WELDING":
                print("HELOOOOOOOOOOOOOOO")
                self.state = "IDLE"
