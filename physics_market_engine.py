import numpy as np
import pandas as pd
import yfinance as yf
import ta
from typing import Dict, List, Tuple
import math
from datetime import datetime, timedelta
import logging

class PhysicsMarketEngine:
    def __init__(self):
        """Initialize the physics-based market simulation engine"""
        self.GRAVITY_CONSTANT = 6.674e-11  # Market gravity constant
        self.MOMENTUM_DECAY = 0.95  # Momentum decay factor
        self.MAGNETIC_STRENGTH = 1.2  # Magnetic field strength
        self.PARTICLE_MASS_BASE = 1000  # Base mass for volume particles
        
    def analyze_gravity_wells(self, symbol: str) -> Dict:
        """Analyze support/resistance as gravitational wells"""
        try:
            # Get stock data
            stock = yf.Ticker(symbol)
            hist = stock.history(period="6mo", interval="1d")
            
            if hist.empty:
                return {'error': 'No data available'}
            
            # Calculate support and resistance levels
            support_levels = self._find_support_levels(hist)
            resistance_levels = self._find_resistance_levels(hist)
            
            # Calculate gravitational field strength for each level
            gravity_wells = []
            current_price = hist['Close'].iloc[-1]
            
            for level in support_levels:
                distance = abs(current_price - level['price'])
                volume_mass = level['volume_strength'] * self.PARTICLE_MASS_BASE
                
                # Calculate gravitational force using F = G*m1*m2/r^2
                if distance > 0:
                    force = (self.GRAVITY_CONSTANT * volume_mass * current_price) / (distance ** 2)
                    
                    gravity_wells.append({
                        'type': 'support',
                        'price': level['price'],
                        'force': force,
                        'mass': volume_mass,
                        'distance': distance,
                        'strength': self._calculate_well_strength(force, distance),
                        'escape_velocity': math.sqrt(2 * force * distance),
                        'event_horizon': distance * 0.05  # 5% of distance as event horizon
                    })
            
            for level in resistance_levels:
                distance = abs(current_price - level['price'])
                volume_mass = level['volume_strength'] * self.PARTICLE_MASS_BASE
                
                if distance > 0:
                    force = (self.GRAVITY_CONSTANT * volume_mass * current_price) / (distance ** 2)
                    
                    gravity_wells.append({
                        'type': 'resistance',
                        'price': level['price'],
                        'force': force,
                        'mass': volume_mass,
                        'distance': distance,
                        'strength': self._calculate_well_strength(force, distance),
                        'escape_velocity': math.sqrt(2 * force * distance),
                        'event_horizon': distance * 0.05
                    })
            
            # Calculate net gravitational field
            net_force = sum([well['force'] if well['type'] == 'support' else -well['force'] 
                           for well in gravity_wells])
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'gravity_wells': sorted(gravity_wells, key=lambda x: x['strength'], reverse=True),
                'net_gravitational_force': net_force,
                'dominant_well': max(gravity_wells, key=lambda x: x['strength']) if gravity_wells else None,
                'field_strength': abs(net_force),
                'field_direction': 'bullish' if net_force > 0 else 'bearish'
            }
            
        except Exception as e:
            logging.error(f"Error in gravity wells analysis: {e}")
            return {'error': str(e)}
    
    def simulate_momentum_particles(self, symbol: str) -> Dict:
        """Simulate price movement as particle physics with momentum"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="3mo", interval="1d")
            
            if hist.empty:
                return {'error': 'No data available'}
            
            # Calculate momentum vectors
            momentum_particles = []
            
            for i in range(len(hist) - 1):
                price_change = hist['Close'].iloc[i+1] - hist['Close'].iloc[i]
                volume = hist['Volume'].iloc[i+1]
                
                # Calculate particle properties
                velocity = price_change / hist['Close'].iloc[i]  # Percentage change as velocity
                mass = volume / 1000000  # Volume as mass (scaled)
                momentum = mass * velocity
                kinetic_energy = 0.5 * mass * (velocity ** 2)
                
                # Calculate particle trajectory
                trajectory = self._calculate_particle_trajectory(velocity, momentum, kinetic_energy)
                
                momentum_particles.append({
                    'date': hist.index[i+1],
                    'price': hist['Close'].iloc[i+1],
                    'velocity': velocity,
                    'mass': mass,
                    'momentum': momentum,
                    'kinetic_energy': kinetic_energy,
                    'trajectory': trajectory,
                    'particle_type': self._classify_particle_type(velocity, momentum),
                    'half_life': self._calculate_momentum_half_life(momentum)
                })
            
            # Analyze particle collisions (reversal points)
            collisions = self._detect_particle_collisions(momentum_particles)
            
            # Calculate momentum field strength
            total_momentum = sum([abs(p['momentum']) for p in momentum_particles[-10:]])
            avg_kinetic_energy = np.mean([p['kinetic_energy'] for p in momentum_particles[-10:]])
            
            return {
                'symbol': symbol,
                'momentum_particles': momentum_particles[-20:],  # Last 20 days
                'particle_collisions': collisions,
                'total_momentum_field': total_momentum,
                'average_kinetic_energy': avg_kinetic_energy,
                'dominant_particle_type': self._get_dominant_particle_type(momentum_particles[-10:]),
                'momentum_conservation': self._check_momentum_conservation(momentum_particles[-5:])
            }
            
        except Exception as e:
            logging.error(f"Error in momentum particles simulation: {e}")
            return {'error': str(e)}
    
    def analyze_magnetic_fields(self, symbol: str) -> Dict:
        """Analyze trend strength as magnetic field effects"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="6mo", interval="1d")
            
            if hist.empty:
                return {'error': 'No data available'}
            
            # Calculate moving averages as magnetic field lines
            ma_20 = hist['Close'].rolling(window=20).mean()
            ma_50 = hist['Close'].rolling(window=50).mean()
            ma_200 = hist['Close'].rolling(window=200).mean()
            
            current_price = hist['Close'].iloc[-1]
            
            # Calculate magnetic field strength based on MA alignment
            field_lines = []
            
            for ma_period, ma_values in [('MA20', ma_20), ('MA50', ma_50), ('MA200', ma_200)]:
                if not ma_values.empty and not pd.isna(ma_values.iloc[-1]):
                    distance = abs(current_price - ma_values.iloc[-1])
                    slope = (ma_values.iloc[-1] - ma_values.iloc[-10]) / 10 if len(ma_values) >= 10 else 0
                    
                    # Calculate magnetic field strength
                    field_strength = self.MAGNETIC_STRENGTH * abs(slope) / (distance + 0.01)
                    
                    field_lines.append({
                        'ma_period': ma_period,
                        'ma_value': ma_values.iloc[-1],
                        'distance_from_price': distance,
                        'slope': slope,
                        'field_strength': field_strength,
                        'field_direction': 'attractive' if slope > 0 else 'repulsive',
                        'magnetic_moment': field_strength * distance
                    })
            
            # Calculate total magnetic field
            total_field = sum([line['field_strength'] for line in field_lines])
            net_direction = sum([line['slope'] for line in field_lines])
            
            # Detect magnetic field reversals (trend changes)
            reversals = self._detect_magnetic_reversals(hist)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'magnetic_field_lines': field_lines,
                'total_field_strength': total_field,
                'net_magnetic_direction': 'bullish' if net_direction > 0 else 'bearish',
                'field_uniformity': self._calculate_field_uniformity(field_lines),
                'magnetic_reversals': reversals,
                'field_stability': self._calculate_field_stability(field_lines)
            }
            
        except Exception as e:
            logging.error(f"Error in magnetic fields analysis: {e}")
            return {'error': str(e)}
    
    def simulate_weather_patterns(self, symbol: str) -> Dict:
        """Simulate market sentiment as weather patterns"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="3mo", interval="1d")
            
            if hist.empty:
                return {'error': 'No data available'}
            
            # Calculate weather metrics
            volatility = hist['Close'].pct_change().rolling(window=20).std() * 100
            volume_pressure = hist['Volume'].rolling(window=10).mean()
            rsi = ta.momentum.RSIIndicator(hist['Close']).rsi()
            
            current_weather = {
                'temperature': rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50,  # RSI as temperature
                'pressure': volume_pressure.iloc[-1] if not pd.isna(volume_pressure.iloc[-1]) else 0,
                'humidity': volatility.iloc[-1] if not pd.isna(volatility.iloc[-1]) else 0,
                'wind_speed': abs(hist['Close'].pct_change().iloc[-1]) * 100 if not pd.isna(hist['Close'].pct_change().iloc[-1]) else 0
            }
            
            # Classify weather pattern
            weather_type = self._classify_weather_pattern(current_weather)
            
            # Generate weather forecast
            forecast = self._generate_weather_forecast(hist, current_weather)
            
            return {
                'symbol': symbol,
                'current_weather': current_weather,
                'weather_type': weather_type,
                'forecast': forecast,
                'storm_probability': self._calculate_storm_probability(current_weather),
                'rainbow_probability': self._calculate_rainbow_probability(current_weather)
            }
            
        except Exception as e:
            logging.error(f"Error in weather patterns simulation: {e}")
            return {'error': str(e)}
    
    def calculate_quantum_tunneling(self, symbol: str) -> Dict:
        """Calculate probability of quantum tunneling through resistance levels"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="6mo", interval="1d")
            
            if hist.empty:
                return {'error': 'No data available'}
            
            current_price = hist['Close'].iloc[-1]
            resistance_levels = self._find_resistance_levels(hist)
            
            tunneling_probabilities = []
            
            for level in resistance_levels:
                barrier_height = level['price'] - current_price
                barrier_width = level['volume_strength']  # Volume as barrier width
                
                if barrier_height > 0:  # Only for resistance above current price
                    # Simplified quantum tunneling probability calculation
                    # P = e^(-2*k*a) where k = sqrt(2m(V-E))/ħ
                    k = math.sqrt(2 * barrier_height * barrier_width) / 100  # Simplified
                    tunneling_prob = math.exp(-2 * k) * 100  # As percentage
                    
                    tunneling_probabilities.append({
                        'resistance_level': level['price'],
                        'barrier_height': barrier_height,
                        'barrier_width': barrier_width,
                        'tunneling_probability': min(tunneling_prob, 100),
                        'quantum_coherence': self._calculate_quantum_coherence(hist, level['price']),
                        'wave_function_collapse_risk': self._calculate_collapse_risk(barrier_height, barrier_width)
                    })
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'tunneling_probabilities': sorted(tunneling_probabilities, 
                                                key=lambda x: x['tunneling_probability'], reverse=True),
                'most_likely_tunnel': max(tunneling_probabilities, 
                                        key=lambda x: x['tunneling_probability']) if tunneling_probabilities else None
            }
            
        except Exception as e:
            logging.error(f"Error in quantum tunneling calculation: {e}")
            return {'error': str(e)}
    
    def _find_support_levels(self, hist: pd.DataFrame) -> List[Dict]:
        """Find support levels with volume strength"""
        lows = hist['Low'].rolling(window=10, center=True).min()
        support_levels = []
        
        for i in range(10, len(hist) - 10):
            if hist['Low'].iloc[i] == lows.iloc[i]:
                # Calculate volume strength at this level
                volume_strength = hist['Volume'].iloc[i-5:i+5].mean() / hist['Volume'].mean()
                
                support_levels.append({
                    'price': hist['Low'].iloc[i],
                    'date': hist.index[i],
                    'volume_strength': volume_strength
                })
        
        return support_levels
    
    def _find_resistance_levels(self, hist: pd.DataFrame) -> List[Dict]:
        """Find resistance levels with volume strength"""
        highs = hist['High'].rolling(window=10, center=True).max()
        resistance_levels = []
        
        for i in range(10, len(hist) - 10):
            if hist['High'].iloc[i] == highs.iloc[i]:
                # Calculate volume strength at this level
                volume_strength = hist['Volume'].iloc[i-5:i+5].mean() / hist['Volume'].mean()
                
                resistance_levels.append({
                    'price': hist['High'].iloc[i],
                    'date': hist.index[i],
                    'volume_strength': volume_strength
                })
        
        return resistance_levels
    
    def _calculate_well_strength(self, force: float, distance: float) -> float:
        """Calculate gravitational well strength"""
        return force / (distance + 0.01) * 1000  # Normalized strength
    
    def _calculate_particle_trajectory(self, velocity: float, momentum: float, energy: float) -> Dict:
        """Calculate particle trajectory based on physics"""
        # Simplified trajectory calculation
        range_estimate = abs(velocity) * momentum * 10  # Simplified range
        max_height = energy * 50  # Simplified max height
        
        return {
            'range': range_estimate,
            'max_height': max_height,
            'trajectory_type': 'parabolic' if velocity != 0 else 'linear'
        }
    
    def _classify_particle_type(self, velocity: float, momentum: float) -> str:
        """Classify particle type based on velocity and momentum"""
        if abs(velocity) > 0.05 and abs(momentum) > 0.1:
            return 'photon'  # High energy, high speed
        elif abs(momentum) > 0.05:
            return 'electron'  # Medium energy
        else:
            return 'neutron'  # Low energy
    
    def _calculate_momentum_half_life(self, momentum: float) -> float:
        """Calculate momentum decay half-life"""
        return abs(momentum) * 10 * self.MOMENTUM_DECAY  # Simplified half-life
    
    def _detect_particle_collisions(self, particles: List[Dict]) -> List[Dict]:
        """Detect particle collisions (price reversals)"""
        collisions = []
        
        for i in range(1, len(particles)):
            prev_momentum = particles[i-1]['momentum']
            curr_momentum = particles[i]['momentum']
            
            # Detect momentum sign change (collision)
            if (prev_momentum > 0 and curr_momentum < 0) or (prev_momentum < 0 and curr_momentum > 0):
                collision_energy = abs(prev_momentum) + abs(curr_momentum)
                
                collisions.append({
                    'date': particles[i]['date'],
                    'price': particles[i]['price'],
                    'collision_energy': collision_energy,
                    'collision_type': 'elastic' if collision_energy > 0.1 else 'inelastic'
                })
        
        return collisions
    
    def _get_dominant_particle_type(self, particles: List[Dict]) -> str:
        """Get dominant particle type in recent data"""
        types = [p['particle_type'] for p in particles]
        return max(set(types), key=types.count) if types else 'neutron'
    
    def _check_momentum_conservation(self, particles: List[Dict]) -> bool:
        """Check if momentum is conserved (simplified)"""
        total_momentum = sum([p['momentum'] for p in particles])
        return abs(total_momentum) < 0.1  # Simplified conservation check
    
    def _detect_magnetic_reversals(self, hist: pd.DataFrame) -> List[Dict]:
        """Detect magnetic field reversals (trend changes)"""
        ma_20 = hist['Close'].rolling(window=20).mean()
        ma_50 = hist['Close'].rolling(window=50).mean()
        
        reversals = []
        
        for i in range(50, len(hist)):
            if not pd.isna(ma_20.iloc[i]) and not pd.isna(ma_50.iloc[i]):
                prev_relationship = ma_20.iloc[i-1] > ma_50.iloc[i-1]
                curr_relationship = ma_20.iloc[i] > ma_50.iloc[i]
                
                if prev_relationship != curr_relationship:
                    reversals.append({
                        'date': hist.index[i],
                        'price': hist['Close'].iloc[i],
                        'reversal_type': 'bullish' if curr_relationship else 'bearish'
                    })
        
        return reversals[-5:]  # Last 5 reversals
    
    def _calculate_field_uniformity(self, field_lines: List[Dict]) -> float:
        """Calculate magnetic field uniformity"""
        if not field_lines:
            return 0
        
        strengths = [line['field_strength'] for line in field_lines]
        avg_strength = np.mean(strengths)
        std_strength = np.std(strengths)
        
        return 1 - (std_strength / (avg_strength + 0.01))  # Uniformity score
    
    def _calculate_field_stability(self, field_lines: List[Dict]) -> float:
        """Calculate magnetic field stability"""
        slopes = [line['slope'] for line in field_lines]
        return 1 - (np.std(slopes) / (np.mean(np.abs(slopes)) + 0.01))
    
    def _classify_weather_pattern(self, weather: Dict) -> str:
        """Classify weather pattern based on metrics"""
        temp = weather['temperature']
        pressure = weather['pressure']
        humidity = weather['humidity']
        wind = weather['wind_speed']
        
        if temp > 70 and pressure > 1000000 and humidity < 2:
            return 'sunny'  # Bullish conditions
        elif temp < 30 and pressure < 500000:
            return 'stormy'  # Bearish conditions
        elif humidity > 5 and wind > 3:
            return 'thunderstorm'  # High volatility
        elif wind < 1 and humidity < 1:
            return 'calm'  # Low volatility
        else:
            return 'cloudy'  # Neutral conditions
    
    def _generate_weather_forecast(self, hist: pd.DataFrame, current_weather: Dict) -> List[Dict]:
        """Generate weather forecast for next few days"""
        # Simplified forecast based on trends
        forecast = []
        
        for i in range(1, 6):  # 5-day forecast
            # Simple trend-based forecast
            temp_change = np.random.normal(0, 5)  # Random temperature change
            new_temp = max(0, min(100, current_weather['temperature'] + temp_change))
            
            forecast.append({
                'day': i,
                'temperature': new_temp,
                'weather_type': self._classify_weather_pattern({
                    'temperature': new_temp,
                    'pressure': current_weather['pressure'],
                    'humidity': current_weather['humidity'],
                    'wind_speed': current_weather['wind_speed']
                })
            })
        
        return forecast
    
    def _calculate_storm_probability(self, weather: Dict) -> float:
        """Calculate probability of market storm"""
        volatility_factor = weather['humidity'] / 10
        volume_factor = weather['pressure'] / 1000000
        momentum_factor = weather['wind_speed'] / 5
        
        storm_prob = (volatility_factor + volume_factor + momentum_factor) / 3
        return min(storm_prob * 100, 100)
    
    def _calculate_rainbow_probability(self, weather: Dict) -> float:
        """Calculate probability of rainbow (recovery after storm)"""
        # Rainbow appears after storm with good conditions
        if weather['humidity'] > 3 and weather['temperature'] > 40:
            return min((weather['temperature'] - 40) * 2, 100)
        return 0
    
    def _calculate_quantum_coherence(self, hist: pd.DataFrame, resistance_level: float) -> float:
        """Calculate quantum coherence near resistance level"""
        # Find price data near resistance level
        near_resistance = hist[abs(hist['Close'] - resistance_level) < resistance_level * 0.02]
        
        if len(near_resistance) < 2:
            return 0
        
        # Calculate coherence based on price behavior consistency
        price_variance = near_resistance['Close'].var()
        coherence = 1 / (1 + price_variance)  # Simplified coherence measure
        
        return min(coherence * 100, 100)
    
    def _calculate_collapse_risk(self, barrier_height: float, barrier_width: float) -> float:
        """Calculate wave function collapse risk"""
        # Higher barriers with less volume support have higher collapse risk
        risk = (barrier_height * 10) / (barrier_width + 0.01)
        return min(risk, 100)