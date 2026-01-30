"""
Background Scheduler untuk generate data secara otomatis
Runs setiap X menit sesuai config

"""

import json
import time
import logging
import signal
import sys
from datetime import datetime
from threading import Event

from data_generator import NFTDataGenerator
from database_integration import SimulatorDatabase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simulator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Global flag untuk graceful shutdown
shutdown_event = Event()

def signal_handler(sig, frame):
    """
    logger.info("Shutdown signal received")
    shutdown_event.set()

def run_background_generator():
    
    # Initialize components
    """
    try:
        generator = NFTDataGenerator()
        db = SimulatorDatabase()
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)
    
    # Get interval from config
    interval_seconds = config['data_generation']['interval_seconds']
    logger.info(f"Generation interval: {interval_seconds} seconds")
    
    generation_count = 0
    
    try:
        while not shutdown_event.is_set():
            try:
                # Generate reading
                reading = generator.generate_next_reading()
                generation_count += 1
                
                # Save to database
                db.save_reading(reading)
                
                # Save to current_state.json
                with open('data/current_state.json', 'w') as f:
                    json.dump(reading, f, indent=2)
                
                logger.info(
                    f"[{generation_count}] Generated and saved: "
                    f"pH={reading['ph']}, TDS={reading['tds']}, Status={reading['status']}"
                )
                
                # Wait for next interval (dengan check shutdown setiap detik)
                for _ in range(interval_seconds):
                    if shutdown_event.is_set():
                        break
                    time.sleep(1)
            
            except Exception as e:
                logger.error(f"Error in generation loop: {e}")
                # Wait a bit before retrying
                time.sleep(10)
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    
    finally:
        # Save final state
        try:
            final_state = generator.get_current_state()
            with open('data/current_state.json', 'w') as f:
                json.dump(final_state, f, indent=2)
            logger.info("Final state saved")
        except Exception as e:
            logger.error(f"Failed to save final state: {e}")
        
        logger.info(f"Background generator stopped. Total generations: {generation_count}")

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run generator
    run_background_generator()
