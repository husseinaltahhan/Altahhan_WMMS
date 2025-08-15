import time, sys, gc
import _thread
import urequests, esp32
from publisher import BoardPublisher
from connection import Connector

name = "esp32_b1"

# ADDED: 24h burn-in window (milliseconds) and timer storage
DAY_S = 24 * 60 * 60 
nvs = esp32.NVS("ota")

# Global variables for connection management
bp = BoardPublisher()  # Create publisher without client initially
network_connection = Connector(name, None, bp)

running_state = "CURRENT"
detection_running = False
stop_signal = False
run_update = False


def burnin_begin(version_label="new"):
    nvs.set_str("pv", version_label)   # pending version label
    nvs.set_i32("pv_up", 0)            # accumulated seconds
    nvs.set_i32("pv_ok", 0)            # 1 when done
    nvs.commit()

def burnin_tick(healthy):
    """
    Call about once per minute.
    If healthy==True, add 60s. If False, add nothing (cumulative policy).
    Returns True once when 24h is reached.
    """
    try:
        pv = nvs.get_str("pv")
    except OSError:
        pv = ""
    if not pv:
        return False  # nothing pending

    try:
        ok = nvs.get_i32("pv_ok")
    except OSError:
        ok = 0
    if ok:
        return True

    if healthy:
        try:
            up = nvs.get_i32("pv_up")
        except OSError:
            up = 0
        up += 60
        nvs.set_i32("pv_up", up)
        if up >= DAY_S:
            nvs.set_i32("pv_ok", 1)
        nvs.commit()
        return up >= DAY_S

    return False

def burnin_finalize_clear():
    """Clear pending state after promotion."""
    try:
        nvs.set_str("pv", "")
        nvs.set_i32("pv_up", 0)
        nvs.set_i32("pv_ok", 0)
        nvs.commit()
    except Exception:
        pass

def get_mode():
    try: return nvs.get_i32("mode")
    except: return 1  # default to CURRENT

def set_mode(m):
    n = int(m)
    nvs.set_i32("mode", n)
    nvs.commit()
    return n





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
            set_mode(mode_select)
            if mode_select != 2:        # <-- add these two lines
                burnin_finalize_clear() # clear pending if we left TESTING
        
    finally:
        detection_running = False
         
def start_detection(publisher):
    global mode_select, detection_running
    
    if detection_running:
        return

    mode_select = get_mode()
    folder = "/app/current" if mode_select == 1 else "/app/new" if mode_select == 2 else "/app/old"
    try:
        _thread.start_new_thread(run_detection, (folder, publisher))
    except Exception as e:
        if mode_select > 0:
            mode_select -= 1
            set_mode(mode_select)
        bp.publish_error("thread start failed: %r" % e)
    
def restart_detection(timeout_ms=3000):
    stop_detection()
    
    t0 = time.ticks_ms()
    while detection_running and time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
        time.sleep_ms(50)
    
    start_detection(bp)  

def ota_detection_update():
    global run_update, mode_select  # ADDED global mode_select
    try:
        file_url = "http://broker.tplinkdns.com:80/detect_straight.py"
        res = urequests.get(file_url)
        update_file = "/app/new/detect_straight.py"
        try:
            # test compile here
            compile(res.text, update_file, "exec")
            with open(update_file, "w") as f:
                f.write(res.text)
                            
            run_update = True
            mode_select = 2
            set_mode(2)
            burnin_begin("new")
            restart_detection()
        
        except SyntaxError as e:
            bp.publish_error("Syntax Error: %r" % e)
            run_update = False
            mode_select = 1
            set_mode(mode_select)
        
        finally:
            res.close()
            
    except Exception as e:
        bp.publish_error("failed to write file: %r" % e)
        run_update = False

network_connection.ota_update = ota_detection_update

def update_successful():
    global mode_select, run_update  # ADDED: clear flags on success
    
    update_file = "/app/new/detect_straight.py"
    current_file = "/app/current/detect_straight.py"
    old_file = "/app/old/detect_straight.py"
    
    try:
        with open(current_file, "rb") as src, open(old_file, "wb") as dst:
            dst.write(src.read())
    except Exception as e:
        bp.publish_error("Failed to update old code with current code: %r" % e)
    
    try: 
        with open(update_file, "rb") as src, open(current_file, "wb") as dst:
            dst.write(src.read())
    except Exception as e:
            bp.publish_error("Failed to update current code with new code: %r" % e)

    mode_select = 1
    set_mode(mode_select)
    run_update = False           # ADDED
    
    restart_detection()

mode_select = get_mode()

# Main Loop
def main_loop():
    """Main program loop with connection monitoring"""
    global bp, running_state, detection_running 
    print("Starting main loop...")
    
    next_tick = time.ticks_add(time.ticks_ms(), 60_000)   

    while True:
        network_connection.run()
        
        if not detection_running:
            start_detection(bp)

        # ADDED: burn-in promotion logic (consecutive 24h while in TESTING mode)
        if time.ticks_diff(time.ticks_ms(), next_tick) >= 0:
            healthy = (mode_select == 2) and detection_running
            if burnin_tick(healthy):
                # reached 24h -> promote and clear NVS
                update_successful()
                burnin_finalize_clear()
                # optional: restart to run the promoted current build immediately
                # restart_detection(1)
            next_tick = time.ticks_add(next_tick, 60_000)

# Initial setup
print("ESP32 Industrial Controller Starting...")
print("Attempting Initial Connection")
main_loop()
