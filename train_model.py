import os
import requests
import pandas as pd
import numpy as np
from app.services.ml_service import MLPredictor

def collect_weather_data():
    """Collect historical weather data from Open-Meteo"""
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        "latitude=-29.4669&longitude=-51.9644"
        "&start_date=2014-01-01&end_date=2024-03-27"
        "&daily=temperature_2m_mean,temperature_2m_min,temperature_2m_max,precipitation_sum"
    )
    response = requests.get(url).json()
    df = pd.DataFrame({
        'tavg': response['daily']['temperature_2m_mean'],
        'tmin': response['daily']['temperature_2m_min'],
        'tmax': response['daily']['temperature_2m_max'],
        'prcp': response['daily']['precipitation_sum']
    }, index=pd.to_datetime(response['daily']['time']))

    df['prcp'] = df['prcp'].fillna(0)
    df['tavg'] = df['tavg'].fillna(df['tavg'].mean())
    df['tmin'] = df['tmin'].fillna(df['tmin'].mean())
    df['tmax'] = df['tmax'].fillna(df['tmax'].mean())
    df['chuva'] = df['prcp'].apply(lambda x: 1 if x > 0 else 0)

    return df

def main():
    print("Collecting historical weather data...")
    df = collect_weather_data()
    print(f"Collected {len(df)} days of data")

    print("Training the rain prediction model...")
    predictor = MLPredictor()
    predictor.retrain_model(df)

    print("Model trained and saved successfully!")

if __name__ == "__main__":
    main()
