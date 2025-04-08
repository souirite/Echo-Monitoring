# backend/src/main.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.plc_connection import PLCConnection

def main():
    plc = PLCConnection()
    try:
        plc.connect()
        plc.start_monitoring(db_number=1020, start_byte=20, end_byte=60, poll_interval=1.0)
        
        print("Monitoring is running in the background.")
        print("Press 'q' and Enter to quit the application.")
        
        # Keep the main thread alive until user quits
        while True:
            user_input = input().strip().lower()
            if user_input == 'q':
                print("Shutting down...")
                break
    
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        plc.stop_monitoring()  # Stop the background thread
        plc.disconnect()      # Disconnect PLC and close database

if __name__ == "__main__":
    main()