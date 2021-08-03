import os
import json
import boto3
import logging
from models.asset_trader import AssetTrader
from models.utils import write_to_s3, download_from_s3

asset = os.getenv('ASSET')
api_secret = os.getenv('API_SECRET')
api_key = os.getenv('API_KEY')
passphrase = os.getenv('PASSPHRASE')
use_sandbox = os.getenv('USE_SANDBOX')

bucket = os.getenv('S3_BUCKET')
model_name = os.getenv('MODEL_NAME')
region_name = os.getenv('REGION_NAME')
trading_history_table = os.getenv('TRADING_HISTORY_TABLE')


def lambda_handler(event, context):
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    joblib_file = '/tmp/model.joblib'
    validation_metrics = '/tmp/validation_metrics.json'

    model_s3_download_response = download_from_s3(
        bucket, 
        os.path.join(model_name, 'model.joblib'), 
        joblib_file
    )
    logging.info('Model Artifact downloaded')

    validation_metrics_download_response = download_from_s3(
        bucket, 
        os.path.join(model_name, 'validation_metrics.json'), 
        validation_metrics
    )
    logging.info('Validation Metrics downloaded')

    with open(validation_metrics, 'r') as val_json_file:
        val_metrics = json.loads(val_json_file.read())
        val_json_file.close()

    asset_trader = AssetTrader(
        asset,
        api_secret,
        api_key,
        passphrase,
        joblib_file,
        use_sandbox
    )
    usd_wallet = asset_trader.get_account_balance(asset_trader.usd_wallet)
    asset_wallet = asset_trader.get_account_balance(asset_trader.asset_wallet)

    start_datetime, end_datetime = asset_trader._get_start_end_iso_times()
    last_hour_asset_values = asset_trader.get_asset_details_last_hour(start=start_datetime, end=end_datetime)
    open_, high_, low_, current_close_, volume_ = last_hour_asset_values.reshape(-1).tolist()
    model_prediction = asset_trader.predict(open_, high_, low_, current_close_, volume_)

    action, amount = asset_trader.trading_strategy(
        model_prediction = model_prediction,
        threshold_to_act = float(validation_metrics['mae']) / 3,
        current_close_price = current_close_,
        percent_of_total_money_to_move = 0.10,
        total_money_in_usd = usd_wallet
    )

    if action == 'buy':
        order_response = asset_trader.place_buy_order(amount)
        logging.info('Made Buy Order')

    elif action == 'sell':
        order_response = asset_trader.place_sell_order(amount)
        logging.info('Made Sell Order')

    elif action == 'do_nothing':
        order_response = None
        logging.info('Not Making an Order')
    
    logging.info('Done')

    return None

    