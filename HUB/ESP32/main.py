import time, sys, gc
import _thread
import urequests
from publisher import BoardPublisher
from connection import Connector

name = "esp32_b1"

# ADDED: 24h burn-in window (milliseconds) and timer storage
BURNIN_MS = 24 * 60 * 60 * 1000
test_start_ms = None

# Global variables for connection management
client = None
bp = BoardPublisher()  # Create publisher without client initially
network_connection = Connector(name, None, bp)

running_state = "CURRENT"
detection_running = False
stop_signal = False
mode_select = 1
run_update = False

def stop_detection():
    global stop_signal
    stop_signal = True

def run_detection(folder, publisher):
    global stop_signal, detection_running, mode_select
    if folder not in sys.path:
        sys.path.insert(0, folder)
    sys.modules.pop("detect_straight", None)
    
    try:
        import detect_straight
        detector = detect_straight.GateWeldingDetector(18, 21)
        network_connection.set_detection(detector)
        detection_running = True
        stop_signal = False
        
        while not stop_signal:
            detector.main(publisher)
            time.sleep_ms(5)
            if gc.mem_free() < 8000:
                gc.collect()
    
    except Exception as e:
        bp.publish_error(e)
        if mode_select > 0:
            mode_select -= 1
        
    finally:
        detection_running = False
         
def start_detection(mode_select, publisher):
    global detection_running
    if detection_running:
        return

    folder = "/app/current" if mode_select == 1 else "/app/new" if mode_select == 2 else "/app/old"
    try:
        _thread.start_new_thread(run_detection, (folder, publisher))
    except Exception as e:
        if mode_select > 0:
            mode_select -= 1
        bp.publish_error("thread start failed: %r" % e)
    
def restart_detection(mode_select, timeout_ms=3000):
    stop_detection()
    
    t0 = time.ticks_ms()
    while detection_running and time.tick_diff(time.ticks_ms(), t0) < timeout_ms:
        time.sleep_ms(50)
    
    start_detection(mode_select, bp)  

def ota_detection_update():
    global run_update, mode_select, test_start_ms  # ADDED test_start_ms/global mode_select
    try:
        file_url = "http://broker.tplinkdns.com:80/detect_straight.py"
        res = urequests.get(file_url)
        update_file = "/app/new/detect_straight.py"
        try:
            # test compile here
            compile(res.text, update_file, "exec")
            with open(update_file, "w") as f:
                f.write(res.text)
            res.close()
            
            run_update = True
            mode_select = 2
            test_start_ms = time.ticks_ms()   # ADDED: start burn-in timer
            restart_detection(mode_select)
        
        except SyntaxError as e:
            bp.publish_error("Syntax Error: %r", e)
            run_update = False
            mode_select = 1
            
    except Exception as e:
        bp.publish_error("failed to write file: %r" % e)
        run_update = False

def update_successful():
    global mode_select, run_update, test_start_ms  # ADDED: clear flags on success
    
    update_file = "/app/new/detect_straight.py"
    current_file = "/app/current/detect_straight.py"
    old_file = "/app/old/detect_straight.py"
    
    with open(current_file, "rb") as src, open(old_file, "wb") as dst:
        dst.write(src.read())
    with open(update_file, "rb") as src, open(current_file, "wb") as dst:
        dst.write(src.read())
    mode_select = 1
    run_update = False           # ADDED
    test_start_ms = None         # ADDED

# Main Loop
def main_loop():
    """Main program loop with connection monitoring"""
    global bp, running_state, detection_running, test_start_ms  # ADDED test_start_ms
    print("Starting main loop...")
    
    while True:
        network_connection.run()
        if not detection_running:
            start_detection(mode_select, bp)

        # ADDED: burn-in promotion logic (consecutive 24h while in TESTING mode)
        if mode_select == 2:
            if detection_running:
                if test_start_ms is None:
                    test_start_ms = time.ticks_ms()
                else:
                    if time.ticks_diff(time.ticks_ms(), test_start_ms) >= BURNIN_MS:
                        update_successful()
                        # optionally restart detection on current, but not required here
            else:
                # detector not running -> reset the consecutive timer
                test_start_ms = None

# Initial setup
print("ESP32 Industrial Controller Starting...")
print("Attempting Initial Connection")
main_loop()
