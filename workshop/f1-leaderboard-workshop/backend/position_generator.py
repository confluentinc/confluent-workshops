import random
import math
from datetime import datetime
from typing import List, Dict, Optional
from models import DriverPosition, F1_DRIVERS

class RealisticPositionGenerator:
    def __init__(self, race_duration: int = 120):
        self.race_duration = race_duration  # 120 seconds (2 minutes)
        self.drivers = F1_DRIVERS
        self.position_history = {}  # Track position history for each driver
        
    def generate_race_positions(self, selected_driver_name: str, race_progress: float) -> List[Dict]:
        """
        Generate realistic positions for all drivers based on race progress.
        
        Args:
            selected_driver_name: Name of the driver to focus on
            race_progress: Progress from 0.0 to 1.0 (0 = start, 1 = finish)
            
        Returns:
            List of position dictionaries for all drivers
        """
        # Initialize position history for this race if not exists
        if selected_driver_name not in self.position_history:
            self.position_history[selected_driver_name] = {
                'starting_position': random.randint(5, 10),
                'positions': []
            }
        
        # Calculate target position for selected driver based on race progress
        starting_pos = self.position_history[selected_driver_name]['starting_position']
        target_position = self._calculate_target_position(starting_pos, race_progress)
        
        
        # Generate positions for all drivers
        positions = []
        used_positions = set()
        
        # First, assign position to selected driver
        selected_driver_pos = self._get_realistic_position(
            selected_driver_name, 
            target_position, 
            used_positions
        )
        
        # Ensure selected driver can reach podium positions (1-3) especially near the end
        if race_progress > 0.8:  # In the final 20% of the race
            if selected_driver_pos > 3 and target_position <= 3:
                # Force the driver into a podium position if they're close to the target
                available_podium = [pos for pos in [1, 2, 3] if pos not in used_positions]
                if available_podium:
                    selected_driver_pos = random.choice(available_podium)
        
        used_positions.add(selected_driver_pos)
        
        # Generate positions for other drivers
        other_drivers = [driver for driver in self.drivers if driver.name != selected_driver_name]
        other_positions = self._generate_other_driver_positions(other_drivers, used_positions)
        
        # Combine all positions
        positions.append({
            'driver_name': selected_driver_name,
            'position': selected_driver_pos,
            'timestamp': datetime.now(),
            'is_selected': True,
            'team_name': self._get_team_name(selected_driver_name),
            'speed': self._generate_speed(selected_driver_pos)
        })
        
        for driver, pos in zip(other_drivers, other_positions):
            positions.append({
                'driver_name': driver.name,
                'position': pos,
                'timestamp': datetime.now(),
                'is_selected': False,
                'team_name': driver.team,
                'speed': self._generate_speed(pos)
            })
        
        # Store position history
        self.position_history[selected_driver_name]['positions'].append({
            'progress': race_progress,
            'position': selected_driver_pos,
            'timestamp': datetime.now()
        })
        
        return positions
    
    def _get_team_name(self, driver_name: str) -> str:
        """Get team name for a driver"""
        for driver in self.drivers:
            if driver.name == driver_name:
                return driver.team
        return "Unknown Team"
    
    def _generate_speed(self, position: int) -> float:
        """Generate realistic speed based on position"""
        # Base speed varies by position - leaders are faster
        if position <= 3:  # Podium positions
            base_speed = 320 + random.uniform(-5, 5)
        elif position <= 7:  # Mid-field
            base_speed = 310 + random.uniform(-8, 8)
        else:  # Back markers
            base_speed = 300 + random.uniform(-10, 10)
        
        return round(base_speed, 1)
    
    
    def _calculate_target_position(self, starting_position: int, race_progress: float) -> int:
        """
        Calculate where the selected driver should be based on race progress.
        Uses a curve that accelerates toward the end.
        """
        if race_progress <= 0:
            return starting_position
        
        if race_progress >= 1.0:
            # Randomly choose final position between 1st, 2nd, or 3rd place
            # Weight it slightly toward better positions for more excitement
            weights = [0.4, 0.35, 0.25]  # 40% chance for 1st, 35% for 2nd, 25% for 3rd
            return random.choices([1, 2, 3], weights=weights)[0]
        
        # Use a quadratic curve for more realistic progression
        # Driver moves slowly at first, then accelerates
        progress_squared = race_progress ** 2
        
        # Calculate how many positions to move (toward podium)
        positions_to_move = starting_position - 1  # From starting pos to P1 (win)
        current_progress = progress_squared * positions_to_move
        
        target = starting_position - int(current_progress)
        return max(1, min(starting_position, target))  # Ensure they can reach podium (1-3)
    
    def _get_realistic_position(self, driver_name: str, target_position: int, used_positions: set) -> int:
        """
        Get a realistic position for the selected driver, considering previous position.
        Now with extremely dynamic and rapid position changes for excitement.
        """
        if driver_name not in self.position_history or not self.position_history[driver_name]['positions']:
            # First position - use target
            return target_position
        
        # Get last position
        last_position = self.position_history[driver_name]['positions'][-1]['position']
        
        # If we're close to the target, be more aggressive about reaching it
        if abs(target_position - last_position) <= 2:
            # High chance to move directly toward target
            if random.random() < 0.7:  # 70% chance to move toward target
                if target_position < last_position:
                    new_position = last_position - 1
                elif target_position > last_position:
                    new_position = last_position + 1
                else:
                    new_position = target_position
            else:
                # Sometimes add some drama
                new_position = target_position + random.randint(-1, 1)
        else:
            # Normal dynamic movement
            position_diff = target_position - last_position
            max_change = random.randint(2, 5)  # More controlled changes
            
            # Add randomness for excitement
            if random.random() < 0.3:  # 30% chance of unexpected movement
                max_change = random.randint(3, 6)
            
            if position_diff > 0:
                # Moving up (worse position number)
                change = random.randint(0, min(max_change, position_diff))
            else:
                # Moving down (better position number) - more likely
                change = random.randint(max(-max_change, position_diff), 0)
            
            new_position = last_position + change
        
        # Ensure position is valid
        new_position = max(1, min(10, new_position))
        
        # If position is taken, try nearby positions
        if new_position in used_positions:
            # Try to find an available position near the target
            for offset in [0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5]:
                candidate = target_position + offset
                if 1 <= candidate <= 10 and candidate not in used_positions:
                    new_position = candidate
                    break
            else:
                # If still no position found, try near current position
                for offset in [0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5]:
                    candidate = last_position + offset
                    if 1 <= candidate <= 10 and candidate not in used_positions:
                        new_position = candidate
                        break
        
        return new_position
    
    def _generate_other_driver_positions(self, drivers: List, used_positions: set) -> List[int]:
        """
        Generate realistic positions for other drivers ensuring unique positions.
        """
        available_positions = [i for i in range(1, 11) if i not in used_positions]
        
        # Shuffle available positions to add randomness
        random.shuffle(available_positions)
        
        # Assign positions ensuring uniqueness
        positions = []
        for i, driver in enumerate(drivers):
            if i < len(available_positions):
                positions.append(available_positions[i])
            else:
                # This should not happen with 10 drivers, but add fallback
                # Find an unused position
                for pos in range(1, 11):
                    if pos not in used_positions and pos not in positions:
                        positions.append(pos)
                        break
        
        return positions
    
    def reset_race(self, selected_driver_name: str):
        """Reset position history for a new race."""
        if selected_driver_name in self.position_history:
            del self.position_history[selected_driver_name]
