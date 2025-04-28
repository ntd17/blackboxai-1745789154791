# Oracles in the Decentralized Painting Contract Platform

## Overview

This platform uses oracles to integrate external data into smart contracts. Two types of oracles are used:

- **Weather API Oracle:** Fetches real-time weather data to influence contract parameters.
- **Machine Learning (ML) Fallback Oracle:** Provides weather predictions when the Weather API is unavailable.

## How the Oracles Work

- The Weather API oracle queries an external weather service to get current weather conditions.
- If the Weather API fails or is unreachable, the ML fallback oracle uses a TensorFlow model to predict weather conditions based on historical data.

## Simulating Oracle Calls Manually

You can simulate oracle calls manually using the following methods:

### Using Curl to Call the Weather API Oracle

```bash
curl -X GET "http://localhost:5000/api/oracle/weather?location=your_location"
```

Replace `your_location` with the desired location.

### Using Python Script to Simulate Oracle Call

```python
import requests

response = requests.get("http://localhost:5000/api/oracle/weather", params={"location": "your_location"})
print(response.json())
```

### Triggering the ML Fallback Oracle

If the Weather API is down, you can manually trigger the ML fallback oracle:

```bash
curl -X POST "http://localhost:5000/api/ml/predict_rain" -H "Content-Type: application/json" -d '{"location": "your_location"}'
```

## Additional Notes

- Ensure your API key for the Weather API is correctly configured in the environment variables.
- Oracle calls are logged for auditing and debugging purposes.

![Weather Oracle](https://images.pexels.com/photos/414171/pexels-photo-414171.jpeg)
