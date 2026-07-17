from futu import *
from datetime import datetime
import indicator
import market
import market_us

def main_loop():
    while True:
        #print("main loop", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        time.sleep(5)

if __name__ == "__main__":
    market.start_indicator_thread()
    market_us.us_start_indicator_thread()

    thread = threading.Thread(target=main_loop)
    thread.start()
    thread.join()

