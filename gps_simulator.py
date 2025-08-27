#!/usr/bin/env python3
"""
GPS Data Simulator

This script simulates realistic GPS data and sends it to the GPS Data Streamer API
for testing purposes. It can simulate multiple devices with realistic movement patterns.
"""

import asyncio
import aiohttp
import json
import random
import logging
from datetime import datetime, timedelta
from typing import List, Tuple
import argparse
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPSSimulator:
    def __init__(self, base_url: str = "http://localhost:8000", devices: int = 1):
        self.base_url = base_url
        self.devices = devices
        self.running = False
        
        # San Francisco area coordinates for realistic simulation
        self.center_lat = 37.7749
        self.center_lon = -122.4194
        self.radius = 0.02  # Roughly 2km radius
        
        # Initialize device states
        self.device_states = {}
        for i in range(devices):
            device_id = f"sim-device-{i+1:03d}"
            self.device_states[device_id] = {
                "latitude": self._random_lat_in_area(),
                "longitude": self._random_lon_in_area(),
                "altitude": random.uniform(0, 100),
                "speed": random.uniform(0, 15),  # m/s (0-54 km/h)
                "heading": random.uniform(0, 360),
                "accuracy": random.uniform(1, 10)
            }
    
    def _random_lat_in_area(self) -> float:
        """Generate random latitude within the simulation area"""
        return self.center_lat + random.uniform(-self.radius, self.radius)
    
    def _random_lon_in_area(self) -> float:
        """Generate random longitude within the simulation area"""
        return self.center_lon + random.uniform(-self.radius, self.radius)
    
    def _update_device_position(self, device_id: str):
        """Update device position with realistic movement"""
        state = self.device_states[device_id]
        
        # Simulate realistic GPS behavior
        # Small random movements with occasional larger jumps
        if random.random() < 0.95:  # 95% small movements
            # Small movement (walking/driving)
            speed_factor = state["speed"] / 111320  # Convert m/s to degrees per second roughly
            
            # Update heading with some randomness (simulate turning)
            state["heading"] += random.uniform(-15, 15)
            state["heading"] = state["heading"] % 360
            
            # Calculate position change based on speed and heading
            heading_rad = math.radians(state["heading"])
            lat_change = math.cos(heading_rad) * speed_factor
            lon_change = math.sin(heading_rad) * speed_factor
            
            state["latitude"] += lat_change
            state["longitude"] += lon_change
            
            # Keep within bounds
            if state["latitude"] < self.center_lat - self.radius:
                state["latitude"] = self.center_lat - self.radius
                state["heading"] = random.uniform(0, 180)  # Turn north
            elif state["latitude"] > self.center_lat + self.radius:
                state["latitude"] = self.center_lat + self.radius
                state["heading"] = random.uniform(180, 360)  # Turn south
                
            if state["longitude"] < self.center_lon - self.radius:
                state["longitude"] = self.center_lon - self.radius
                state["heading"] = random.uniform(270, 450) % 360  # Turn east
            elif state["longitude"] > self.center_lon + self.radius:
                state["longitude"] = self.center_lon + self.radius
                state["heading"] = random.uniform(90, 270)  # Turn west
            
        else:  # 5% larger jumps (simulate faster movement)
            state["latitude"] += random.uniform(-0.001, 0.001)
            state["longitude"] += random.uniform(-0.001, 0.001)
            state["heading"] = random.uniform(0, 360)
        
        # Update other parameters
        state["speed"] = max(0, state["speed"] + random.uniform(-2, 2))
        state["speed"] = min(50, state["speed"])  # Cap at 50 m/s
        
        state["altitude"] = max(0, state["altitude"] + random.uniform(-5, 5))
        state["altitude"] = min(1000, state["altitude"])  # Cap at 1000m
        
        state["accuracy"] = max(1, random.uniform(1, 15))
    
    def _generate_gps_data(self, device_id: str) -> dict:
        """Generate GPS data for a device"""
        self._update_device_position(device_id)
        state = self.device_states[device_id]
        
        return {
            "device_id": device_id,
            "latitude": round(state["latitude"], 6),
            "longitude": round(state["longitude"], 6),
            "altitude": round(state["altitude"], 1),
            "speed": round(state["speed"], 1),
            "heading": round(state["heading"], 1),
            "accuracy": round(state["accuracy"], 1),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    async def send_gps_data(self, session: aiohttp.ClientSession, gps_data: dict) -> bool:
        """Send GPS data to the API"""
        try:
            url = f"{self.base_url}/api/gps/data"
            async with session.post(url, json=gps_data) as response:
                if response.status == 200:
                    logger.debug(f"Successfully sent data for {gps_data['device_id']}")
                    return True
                elif response.status == 429:  # Rate limited
                    logger.debug(f"Rate limited for {gps_data['device_id']}")
                    return False
                else:
                    error_text = await response.text()
                    logger.warning(f"Failed to send data for {gps_data['device_id']}: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending data for {gps_data['device_id']}: {str(e)}")
            return False
    
    async def run_simulation(self, duration_seconds: int = None, rate_per_second: float = 1.0):
        """Run the GPS simulation"""
        self.running = True
        logger.info(f"Starting GPS simulation with {self.devices} devices")
        logger.info(f"Rate: {rate_per_second} requests/second, Duration: {duration_seconds or 'infinite'} seconds")
        
        start_time = datetime.now()
        iteration = 0
        
        async with aiohttp.ClientSession() as session:
            while self.running:
                iteration += 1
                
                # Generate and send data for all devices
                tasks = []
                for device_id in self.device_states.keys():
                    gps_data = self._generate_gps_data(device_id)
                    tasks.append(self.send_gps_data(session, gps_data))
                
                # Execute all requests concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                success_count = sum(1 for r in results if r is True)
                logger.info(f"Iteration {iteration}: {success_count}/{len(tasks)} requests successful")
                
                # Check if we should stop
                if duration_seconds:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed >= duration_seconds:
                        break
                
                # Wait for next iteration (respecting rate limit)
                await asyncio.sleep(1.0 / rate_per_second)
        
        logger.info("GPS simulation stopped")
    
    def stop(self):
        """Stop the simulation"""
        self.running = False

async def main():
    parser = argparse.ArgumentParser(description="GPS Data Simulator")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the GPS Data Streamer API")
    parser.add_argument("--devices", type=int, default=1,
                       help="Number of devices to simulate")
    parser.add_argument("--duration", type=int, default=60,
                       help="Duration in seconds (0 for infinite)")
    parser.add_argument("--rate", type=float, default=1.0,
                       help="Requests per second per device")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    simulator = GPSSimulator(base_url=args.url, devices=args.devices)
    
    try:
        await simulator.run_simulation(
            duration_seconds=args.duration if args.duration > 0 else None,
            rate_per_second=args.rate
        )
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
        simulator.stop()

if __name__ == "__main__":
    asyncio.run(main())