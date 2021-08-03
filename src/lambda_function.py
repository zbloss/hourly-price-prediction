import os
import boto3
from models.asset_trader import AssetTrader

asset = os.getenv('ASSET')
api_secret = os.getenv('API_SECRET')
api_key = os.getenv('API_KEY')
passphrase = os.getenv('PASSPHRASE')
joblib_file = os.getenv('JOBLIB_FILE')
use_sandbox = os.getenv('USE_SANDBOX')

def lambda_handler(event, context):

    asset_trader = AssetTrader(
        asset,
        api_secret,
        api_key,
        passphrase,
        joblib_file,
        use_sandbox
    )

    start_datetime, end_datetime = asset_trader._get_start_end_iso_times()
    last_hour_asset_values = asset_trader.get_asset_details_last_hour(start=start_datetime, end=end_datetime)
    open_, high_, low_, current_close_, volume_ = last_hour_asset_values.reshape(-1).tolist()

    model_prediction = asset_trader.predict(open_, high_, low_, current_close_, volume_)

    action, amount = asset_trader.trading_strategy(
        model_prediction = model_prediction,
        threshold_to_act = 0,
        current_close_price = current_close_,
        percent_of_total_money_to_move = 0.10,
        total_money_in_usd = 
    )

    print('Hello World')
    return None

    