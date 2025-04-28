# Machine Learning Guide for Rain Prediction

## Overview

This guide explains how to train, export, and update the TensorFlow model used by the `/api/ml/predict_rain` endpoint.

## Training the TensorFlow Model

1. Prepare your dataset with historical weather data including rain, temperature, and other relevant features.

2. Use the training script (example):

```python
import tensorflow as tf

# Load and preprocess data
# Define model architecture
# Train model
model.fit(train_data, epochs=10)

# Save the model
model.save('path/to/model')
```

Alternatively, you can use the provided training script `train_model.py` in the project root to automate data collection and model training:

```bash
python train_model.py
```

This script downloads historical weather data from Open-Meteo, preprocesses it, trains a binary classifier to predict rain, and saves the model as `ml_rain_predictor.h5` in the project root.

## Exporting the Model

Export the trained model in a format compatible with the Flask API:

```python
model.save('app/data/ml_models/rain_prediction_model')
```

## Updating the Model in the API

- Replace the existing model files in `app/data/ml_models/` with the new exported model.
- Restart the Flask application to load the updated model.

## Example Usage

The `/api/ml/predict_rain` endpoint uses this model to predict rain probability based on input features.

## Tips

- Regularly retrain the model with new data for improved accuracy.
- Monitor model performance and update as needed.

![Machine Learning](https://images.pexels.com/photos/256658/pexels-photo-256658.jpeg)
