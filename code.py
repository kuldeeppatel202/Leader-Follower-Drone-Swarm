import json
import hashlib
import math

class Drone:
    def __init__(self, id, role, mass, initial_velocity=(0, 0, 0), gps_coordinates=(0, 0), altitude=0):
        self.id = id
        self.role = role  # 'leader' or 'follower'
        self.mass = mass
        self.velocity = {"x": initial_velocity[0], "y": initial_velocity[1], "z": initial_velocity[2]}
        self.acceleration = {"x": 0, "y": 0, "z": 0}
        self.gps_coordinates = {"latitude": gps_coordinates[0], "longitude": gps_coordinates[1]}
        self.altitude = altitude
        self.received_messages = []
    
    def send_position_update(self, followers):
        # Leader sends its current position to all followers
        if self.role != 'leader':
            print(f"Drone {self.id} is not a leader and cannot send position updates.")
            return
        
        position_payload = {
            "gps_coordinates": self.gps_coordinates,
            "altitude": self.altitude
        }
        message = self.create_message("Position Update", position_payload, [f.id for f in followers])
        for follower in followers:
            print(f"Drone {self.id} sending position update to Drone {follower.id}")
            follower.receive_message(message)
    
    def receive_message(self, message):
        # Verify the checksum before processing
        if self.verify_checksum(message):
            self.received_messages.append(message)
            print(f"Drone {self.id} received message: {message}")
            self.process_message(message)
        else:
            print(f"Drone {self.id} received corrupted message")
    
    def process_message(self, message):
        # Process the received message based on its type
        message_type = message['header']['message_type']
        payload = message['payload']
        
        if message_type == "Position Update" and self.role == 'follower':
            leader_position = payload
            self.adjust_position(leader_position)
    
    def adjust_position(self, leader_position):
        # Calculate distance to the leader
        distance = self.calculate_distance(leader_position)
        print(f"Drone {self.id} current distance to leader: {distance:.2f} meters")
        
        # Desired distance
        desired_distance = 3.0  # meters
        if distance == desired_distance:
            print(f"Drone {self.id} is at the desired distance from the leader.")
            return
        
        # Calculate the direction vector from follower to leader
        delta_lat = leader_position['gps_coordinates']['latitude'] - self.gps_coordinates['latitude']
        delta_long = leader_position['gps_coordinates']['longitude'] - self.gps_coordinates['longitude']
        delta_alt = leader_position['altitude'] - self.altitude
        
        # Calculate unit vector
        vector_length = math.sqrt(delta_lat**2 + delta_long**2 + delta_alt**2)
        unit_vector = {
            'latitude': delta_lat / vector_length,
            'longitude': delta_long / vector_length,
            'altitude': delta_alt / vector_length
        }
        
        # Calculate new position
        adjustment = (distance - desired_distance)
        self.gps_coordinates['latitude'] += unit_vector['latitude'] * adjustment
        self.gps_coordinates['longitude'] += unit_vector['longitude'] * adjustment
        self.altitude += unit_vector['altitude'] * adjustment
        
        print(f"Drone {self.id} adjusted position to GPS: {self.gps_coordinates}, Altitude: {self.altitude:.2f}")
    
    def calculate_distance(self, leader_position):
        # Approximate conversion from degrees to meters (for small distances)
        lat_diff = (leader_position['gps_coordinates']['latitude'] - self.gps_coordinates['latitude']) * 111139  # meters per degree latitude
        long_diff = (leader_position['gps_coordinates']['longitude'] - self.gps_coordinates['longitude']) * 111139 * math.cos(math.radians(self.gps_coordinates['latitude']))
        alt_diff = leader_position['altitude'] - self.altitude
        distance = math.sqrt(lat_diff**2 + long_diff**2 + alt_diff**2)
        return distance
    
    def create_message(self, message_type, payload, destination_ids):
        # Create a message with a header, payload, and checksum
        message = {
            "header": {
                "message_type": message_type,
                "source_id": self.id,
                "destination_ids": destination_ids
            },
            "payload": payload,
            "checksum": self.calculate_checksum(payload)
        }
        return message
    
    def calculate_checksum(self, payload):
        # Generate a checksum for the payload
        data = json.dumps(payload, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()
    
    def verify_checksum(self, message):
        # Calculate and check checksum
        data = json.dumps(message["payload"], sort_keys=True)
        checksum = hashlib.md5(data.encode()).hexdigest()
        return checksum == message["checksum"]
    
    def update_position(self, delta_latitude, delta_longitude, delta_altitude):
        # Update the drone's GPS coordinates and altitude
        self.gps_coordinates['latitude'] += delta_latitude
        self.gps_coordinates['longitude'] += delta_longitude
        self.altitude += delta_altitude
        print(f"Drone {self.id} moved to GPS: {self.gps_coordinates}, Altitude: {self.altitude:.2f}")


# Initialize drones
drone_a = Drone(id="A", role="leader", mass=1.5, gps_coordinates=(28.7041, 77.1025), altitude=100)
drone_b = Drone(id="B", role="follower", mass=2.0, gps_coordinates=(28.7040, 77.1024), altitude=100)
drone_c = Drone(id="C", role="follower", mass=1.8, gps_coordinates=(28.7042, 77.1026), altitude=100)

# List of followers
followers = [drone_b, drone_c]

# Leader sends initial position update
drone_a.send_position_update(followers)

# Simulate leader moving
drone_a.update_position(delta_latitude=0.00001, delta_longitude=0.00001, delta_altitude=0)

# Leader sends updated position
drone_a.send_position_update(followers)
