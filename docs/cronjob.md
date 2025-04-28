# Cronjob Guide for Contract Updates

## Manually Triggering the Cronjob

You can manually trigger the contract update cronjob using the Flask CLI command:

```bash
flask update_contracts
```

Or if using the script directly:

```bash
python -m app.cli.contract_adjuster
```

## Scheduling the Cronjob with APScheduler

To schedule automatic daily execution, use APScheduler in your Flask app:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.cli.contract_adjuster import update_contracts

scheduler = BackgroundScheduler()
scheduler.add_job(func=update_contracts, trigger="interval", days=1)
scheduler.start()
```

Make sure to start the scheduler when your Flask app starts.

## Tips

- Ensure the scheduler runs in the background without blocking the main app.
- Monitor logs to verify cronjob execution.
- Adjust the interval as needed for your use case.

![Scheduler](https://images.pexels.com/photos/669615/pexels-photo-669615.jpeg)
