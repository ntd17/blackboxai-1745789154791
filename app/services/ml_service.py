import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
from flask import current_app

# Only try to import tensorflow if not in test environment
TENSORFLOW_AVAILABLE = False
if not os.environ.get('TESTING'):
    try:
        import tensorflow as tf
        from sklearn.model_selection import train_test_split
        TENSORFLOW_AVAILABLE = True
    except ImportError:
        pass

class MockMLPredictor:
    """Mock ML predictor for testing"""
    def predict_duration(self, features: Dict) -> int:
        """Mock prediction of contract duration"""
        return 7  # Default prediction of 7 days
    
    def predict_weather_impact(self, weather_data: Dict) -> float:
        """Mock prediction of weather impact"""
        return 0.0  # No weather impact in mock

class MLPredictor:
    """ML predictor for contract duration and weather impact"""
    def __init__(self):
        if not TENSORFLOW_AVAILABLE:
            self._mock = MockMLPredictor()
        else:
            model_path = current_app.config.get('ML_MODEL_PATH')
            if model_path and os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
            else:
                self._mock = MockMLPredictor()
    
    def predict_duration(self, features: Dict) -> int:
        """
        Predict contract duration in days
        
        Args:
            features: Dictionary of contract features
            
        Returns:
            int: Predicted duration in days
        """
        if not hasattr(self, 'model'):
            return self._mock.predict_duration(features)
            
        try:
            # Convert features to model input format
            input_data = self._prepare_features(features)
            prediction = self.model.predict(input_data)
            return int(round(prediction[0]))
        except Exception as e:
            current_app.logger.error(f"ML prediction failed: {str(e)}")
            return self._mock.predict_duration(features)
    
    def predict_weather_impact(self, weather_data: Dict) -> float:
        """
        Predict weather impact on contract duration
        
        Args:
            weather_data: Dictionary of weather forecasts
            
        Returns:
            float: Predicted impact factor (0.0 to 1.0)
        """
        if not hasattr(self, 'model'):
            return self._mock.predict_weather_impact(weather_data)
            
        try:
            # Process weather data for prediction
            impact = self._analyze_weather(weather_data)
            return min(max(impact, 0.0), 1.0)  # Clamp between 0 and 1
        except Exception as e:
            current_app.logger.error(f"Weather impact prediction failed: {str(e)}")
            return self._mock.predict_weather_impact(weather_data)
    
    def _prepare_features(self, features: Dict) -> np.ndarray:
        """Prepare features for model input"""
        # Feature preparation logic here
        return np.array([[
            features.get('area', 0),
            features.get('complexity', 1),
            features.get('workers', 1)
        ]])
    
    def _analyze_weather(self, weather_data: Dict) -> float:
        """Analyze weather data for impact prediction"""
        # Weather analysis logic here
        return 0.0

    def retrain_model(self, df):
        """
        Retrain the rain prediction model using historical weather data DataFrame.
        
        Args:
            df (pandas.DataFrame): DataFrame with columns ['tavg', 'tmin', 'tmax', 'prcp', 'chuva']
        """
        if not TENSORFLOW_AVAILABLE:
            current_app.logger.warning("TensorFlow not available, skipping model retraining.")
            return
        
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Dense, Dropout
        from tensorflow.keras.optimizers import Adam
        from sklearn.model_selection import train_test_split
        
        try:
            # Extract features and target
            X = df[['tavg', 'tmin', 'tmax', 'prcp']].values
            y = df['chuva'].values
            
            # Split data into train and test sets
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Build the model
            model = Sequential([
                Dense(32, activation='relu', input_shape=(4,)),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dropout(0.2),
                Dense(1, activation='sigmoid')
            ])
            
            model.compile(optimizer=Adam(), loss='binary_crossentropy', metrics=['accuracy'])
            
            # Train the model
            model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_test, y_test), verbose=1)
            
            # Save the model
            model_path = os.path.join(os.getcwd(), 'ml_rain_predictor.h5')
            model.save(model_path)
            
            # Update the model attribute
            self.model = model
            
            current_app.logger.info(f"Model retrained and saved to {model_path}")
        
        except Exception as e:
            current_app.logger.error(f"Failed to retrain model: {str(e)}")
