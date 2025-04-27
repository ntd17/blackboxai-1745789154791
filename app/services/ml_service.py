import tensorflow as tf
import numpy as np
from flask import current_app
from typing import Dict, List, Optional
import json
from datetime import datetime
import os

class MLPredictor:
    """Service for making weather-based duration predictions using TensorFlow"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.model_version = "1.0.0"
        self._load_model()
        
    def _load_model(self):
        """Load the TensorFlow model"""
        try:
            if os.path.exists(self.model_path):
                self.model = tf.keras.models.load_model(self.model_path)
            else:
                # If model doesn't exist, create and save a new one
                self._create_initial_model()
                
        except Exception as e:
            current_app.logger.error(f"Failed to load ML model: {str(e)}")
            self._create_initial_model()
    
    def _create_initial_model(self):
        """Create and save initial model if none exists"""
        try:
            # Create a simple sequential model
            self.model = tf.keras.Sequential([
                tf.keras.layers.Dense(64, activation='relu', input_shape=(7,)),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(16, activation='relu'),
                tf.keras.layers.Dense(1)  # Predicted additional days needed
            ])
            
            self.model.compile(
                optimizer='adam',
                loss='mse',
                metrics=['mae']
            )
            
            # Save the model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save(self.model_path)
            
        except Exception as e:
            current_app.logger.error(f"Failed to create initial ML model: {str(e)}")
            raise
    
    def _preprocess_weather_data(self, weather_data: List[Dict]) -> np.ndarray:
        """
        Preprocess weather data for model input
        
        Args:
            weather_data: List of daily weather forecasts
            
        Returns:
            np.ndarray: Preprocessed features
        """
        features = []
        
        for day in weather_data:
            daily_features = [
                day['temp']['day'],          # Average temperature
                day['temp']['max'],          # Maximum temperature
                day['temp']['min'],          # Minimum temperature
                day['humidity'],             # Humidity
                day['wind_speed'],           # Wind speed
                day['rain_prob'],            # Rain probability
                day['rain_amount']           # Rain amount
            ]
            features.append(daily_features)
            
        # Calculate average features across all days
        avg_features = np.mean(features, axis=0)
        return avg_features.reshape(1, -1)
    
    def _calculate_confidence(self, prediction: float, features: np.ndarray) -> float:
        """
        Calculate confidence score for the prediction
        
        Args:
            prediction: Model's prediction
            features: Input features
            
        Returns:
            float: Confidence score between 0 and 1
        """
        try:
            # Make multiple predictions with dropout enabled
            predictions = []
            for _ in range(10):
                pred = self.model(features, training=True)
                predictions.append(pred.numpy()[0][0])
            
            # Calculate standard deviation of predictions
            std_dev = np.std(predictions)
            
            # Convert std dev to confidence score (inverse relationship)
            confidence = 1 / (1 + std_dev)
            
            return float(min(max(confidence, 0), 1))
            
        except Exception as e:
            current_app.logger.error(f"Failed to calculate confidence: {str(e)}")
            return 0.5  # Default medium confidence
    
    def predict_duration(self, weather_data: List[Dict], location: Dict,
                        original_duration: int) -> Dict:
        """
        Predict painting duration based on weather forecast
        
        Args:
            weather_data: List of daily weather forecasts
            location: Dictionary containing location details
            original_duration: Original planned duration in days
            
        Returns:
            dict: Prediction results including recommended duration
        """
        try:
            # Preprocess weather data
            features = self._preprocess_weather_data(weather_data)
            
            # Make prediction
            prediction = self.model.predict(features)[0][0]
            
            # Calculate confidence score
            confidence = self._calculate_confidence(prediction, features)
            
            # Calculate rain probability
            rain_probs = [day['rain_prob'] for day in weather_data]
            avg_rain_prob = sum(rain_probs) / len(rain_probs)
            
            # Calculate recommended duration
            delay_days = max(0, round(prediction))
            recommended_duration = original_duration + delay_days
            
            # Prepare metadata
            metadata = {
                'location': location,
                'original_duration': original_duration,
                'weather_summary': {
                    'avg_rain_probability': avg_rain_prob,
                    'total_rain_days': sum(1 for p in rain_probs if p > 0.5),
                    'prediction_date': datetime.utcnow().isoformat()
                },
                'model_info': {
                    'version': self.model_version,
                    'features_used': [
                        'temperature',
                        'humidity',
                        'wind_speed',
                        'rain_probability',
                        'rain_amount'
                    ]
                }
            }
            
            return {
                'delay_days': delay_days,
                'recommended_duration': recommended_duration,
                'rain_probability': avg_rain_prob,
                'confidence_score': confidence,
                'model_version': self.model_version,
                'metadata': metadata
            }
            
        except Exception as e:
            current_app.logger.error(f"Duration prediction failed: {str(e)}")
            # Return conservative estimate on failure
            return {
                'delay_days': round(original_duration * 0.2),  # 20% buffer
                'recommended_duration': round(original_duration * 1.2),
                'rain_probability': 0.5,
                'confidence_score': 0.3,
                'model_version': self.model_version,
                'metadata': {
                    'error': str(e),
                    'fallback': True
                }
            }
    
    def update_model(self, actual_data: List[Dict]):
        """
        Update model with actual completion data
        
        Args:
            actual_data: List of dictionaries containing actual completion data
                Each dict should have:
                - weather_data: Original weather data
                - original_duration: Planned duration
                - actual_duration: Actual completion duration
        """
        try:
            # Prepare training data
            X = []
            y = []
            
            for data in actual_data:
                features = self._preprocess_weather_data(data['weather_data'])
                X.append(features[0])  # Remove batch dimension
                y.append(data['actual_duration'] - data['original_duration'])
            
            X = np.array(X)
            y = np.array(y)
            
            # Update model
            self.model.fit(
                X, y,
                epochs=5,
                batch_size=32,
                verbose=0
            )
            
            # Save updated model
            self.model.save(self.model_path)
            
        except Exception as e:
            current_app.logger.error(f"Model update failed: {str(e)}")
