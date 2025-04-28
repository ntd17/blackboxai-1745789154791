import click
from flask.cli import with_appcontext
from datetime import datetime, timedelta
from app.models.contract import Contract, ContractAdjustment
from app.services.weather_service import WeatherService
from app.services.ml_service import MLPredictor
from app.utils.logger import get_logger
from app import db

logger = get_logger()

@click.command('adjust_contracts')
@with_appcontext
def adjust_contracts():
    """
    CLI command to adjust contract durations daily based on weather forecasts or ML predictions.
    """
    logger.info("Starting daily contract adjustment process")
    try:
        today = datetime.utcnow().date()
        # Query contracts in progress (status signed and current date within planned period)
        contracts = Contract.query.filter(
            Contract.status == 'signed',
            Contract.planned_start_date <= today
        ).all()

        weather_service = WeatherService()
        ml_predictor = MLPredictor(model_path='app/models/ml_model')

        for contract in contracts:
            try:
                # Calculate remaining days
                elapsed_days = (today - contract.planned_start_date).days
                remaining_days = max(0, (contract.adjusted_duration_days or contract.planned_duration_days) - elapsed_days)
                if remaining_days <= 0:
                    logger.info(f"Contract {contract.id} already completed or no remaining days")
                    continue

                # Fetch real weather forecast for remaining period
                forecast = weather_service.get_forecast(contract.location, today, remaining_days)
                if forecast and any(day.get('rain_prob', 0) > 0.5 for day in forecast):
                    # Calculate delay days (+2 days per rainy day)
                    rainy_days = sum(1 for day in forecast if day.get('rain_prob', 0) > 0.5)
                    delay_days = rainy_days * 2
                    new_duration = (contract.adjusted_duration_days or contract.planned_duration_days) + delay_days

                    # Update contract duration on-chain and off-chain
                    contract.adjusted_duration_days = new_duration
                    contract.adjust_duration(new_duration, reason='Auto-adjusted due to real weather forecast')
                    db.session.commit()

                    logger.info(f"Contract {contract.id} auto-adjusted by {delay_days} days due to rain forecast")
                    # TODO: Add blockchain on-chain update call here

                else:
                    # No real forecast or no rain predicted, fallback to ML prediction
                    ml_result = ml_predictor.predict_duration(
                        weather_data=forecast or [],
                        location=contract.location,
                        original_duration=contract.planned_duration_days
                    )
                    if ml_result['delay_days'] > 0:
                        # Notify parties only, no auto-adjust during execution
                        logger.info(f"Contract {contract.id} ML prediction suggests delay of {ml_result['delay_days']} days - notification sent")
                        # TODO: Implement notification logic here

            except Exception as e:
                logger.error(f"Error processing contract {contract.id}: {str(e)}")
                db.session.rollback()

    except Exception as e:
        logger.error(f"Failed to run contract adjustment process: {str(e)}")

    logger.info("Daily contract adjustment process completed")
