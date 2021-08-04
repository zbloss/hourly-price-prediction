import os
import time
import json
import boto3
import logging
from hourly_price_prediction.models.asset_trader import AssetTrader
from hourly_price_prediction.data.s3_helper import S3Helper
from hourly_price_prediction.models.utils import write_to_s3, download_from_s3

asset = str(os.getenv("ASSET"))
api_secret = str(os.getenv("API_SECRET"))
api_key = str(os.getenv("API_KEY"))
passphrase = str(os.getenv("PASSPHRASE"))
use_sandbox = bool(os.getenv("USE_SANDBOX"))

bucket = str(os.getenv("S3_BUCKET"))
model_name = str(os.getenv("MODEL_NAME"))
region_name = str(os.getenv("AWS_REGION"))


def lambda_handler(event, context):
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    joblib_file = "/tmp/model.joblib"
    validation_metrics = "/tmp/validation_metrics.json"

    data_helper = S3Helper(bucket, region_name)

    data_helper.download_from_s3(
        s3_key=os.path.join(model_name, "model.joblib"), local_filepath=joblib_file
    )
    logging.info("Model Artifact downloaded")

    data_helper.download_from_s3(
        s3_key=os.path.join(model_name, "validation_metrics.json"),
        local_filepath=validation_metrics,
    )
    logging.info("Validation Metrics downloaded")

    with open(validation_metrics, "r") as val_json_file:
        val_metrics = json.loads(val_json_file.read())
        val_json_file.close()

    asset_trader = AssetTrader(
        asset, api_secret, api_key, passphrase, joblib_file, use_sandbox
    )
    usd_wallet = asset_trader.get_account_balance(asset_trader.usd_wallet)
    asset_wallet = asset_trader.get_account_balance(asset_trader.asset_wallet)

    start_datetime, end_datetime = asset_trader._get_start_end_iso_times()
    last_hour_asset_values = asset_trader.get_asset_details_last_hour(
        start=start_datetime, end=end_datetime
    )
    open_, high_, low_, current_close_, volume_ = last_hour_asset_values.reshape(
        -1
    ).tolist()
    model_prediction = asset_trader.predict(open_, high_, low_, current_close_, volume_)

    action, amount = asset_trader.trading_strategy(
        model_prediction=model_prediction,
        threshold_to_act=float(validation_metrics["mae"]) / 3,
        current_close_price=current_close_,
        percent_of_total_money_to_move=0.10,
        total_money_in_usd=usd_wallet,
    )

    if action == "buy":
        order_response = asset_trader.place_buy_order(amount)
        logging.info("Made Buy Order")

    elif action == "sell":
        order_response = asset_trader.place_sell_order(amount)
        logging.info("Made Sell Order")

    elif action == "do_nothing":
        order_response = None
        logging.info("Not Making an Order")

    time.sleep(10)
    usd_wallet = asset_trader.get_account_balance(asset_trader.usd_wallet)
    asset_wallet = asset_trader.get_account_balance(asset_trader.asset_wallet)

    trading_history = {
        "model": model_name,
        "open": open_,
        "high": high_,
        "low": low_,
        "close": current_close_,
        "volume": volume_,
        "model_prediction": model_prediction,
        "action": action,
        "usd_wallet": usd_wallet,
        "asset_wallet": asset_wallet,
    }
    for key in order_response.keys():
        trading_history[key] = order_response[key]

    s3_partition = data_helper.generate_partition()
    trading_history_filename = "{}.json".format(time.strftime("%Y%m%dT%H%M%S%MS"))
    with open(f"/tmp/{trading_history_filename}", "w") as history_jfile:
        history_jfile.write(json.dumps(trading_history))
        history_jfile.close()

    data_helper.upload_to_s3(
        s3_key=f"trading_history/{s3_partition}/{trading_history_filename}",
        local_filepath="/tmp/{trading_history_filename}",
    )

    logging.info("Done")

    return None