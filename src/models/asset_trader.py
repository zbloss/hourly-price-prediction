import time
import cbpro
import joblib
import pandas as pd
from datetime import datetime, timedelta
from joblib import load
from urllib3.exceptions import ProtocolError, ConnectionError


class AssetTrader(object):
    def __init__(
        self,
        asset: str,
        api_secret: str,
        api_key: str,
        passphrase: str,
        joblib_file: str,
        use_sandbox: bool = True,
    ):
        self.asset = asset
        self.api_secret = api_secret
        self.public_client = cbpro.PublicClient()
        api_url = ""
        if use_sandbox:
            api_url = "https://api-public.sandbox.pro.coinbase.com"
        else:
            api_url = "https://api.pro.coinbase.com"

        self.private_client = cbpro.AuthenticatedClient(
            key=api_key,
            b64secret=api_secret.encode(),
            passphrase=passphrase,
            api_url=api_url,
        )
        self.accounts = self.private_client.get_accounts()
        for account in self.accounts:
            if account["currency"] == "USD":
                self.usd_wallet = account["id"]
            elif account["currency"] == self.asset.split("-")[0]:
                self.asset_wallet = account["id"]

        self.model = joblib.load(joblib_file)

    def _get_start_end_iso_times(self, hours: int = 1):
        """
        From the current iso formatted timestamp, this generates
        a start and end datetime that are 1 hour apart.

        :returns: (tuple) Contains (start, end) datetimes.
        """

        time_data = self.public_client.get_time()

        end_datetime = datetime.fromtimestamp(time_data["epoch"])
        start_datetime = end_datetime - timedelta(hours=hours)

        end_iso = end_datetime.isoformat()
        start_iso = start_datetime.isoformat()
        return (start_iso, end_iso)

    def get_asset_details_last_hour(
        self, start: str, end: str, granularity: int = 3600
    ):
        """
        Retrieves hourly open, high, low, close, and volume for the given asset
        over the time range on start to end broken into granularity seconds.

        :param start: (str) ISO-8601 formatted timestamp.
        :param end: (str) ISO-8601 formatted timestamp.
        :param granularity: (int) Number of seconds per interval between start and end.
        :returns: (np.array) Array containing the detailed asset price data.
        """
        try:
            historic_data = self.public_client.get_product_historic_rates(
                product_id=self.asset, start=start, end=end, granularity=granularity
            )
        except (ProtocolError, ConnectionError):
            time.sleep(5)
            historic_data = self.public_client.get_product_historic_rates(
                product_id=self.asset, start=start, end=end, granularity=granularity
            )
        historic_data = pd.DataFrame(
            historic_data,
            columns=["timestamp", "low", "high", "open", "close", "volume"],
        )
        historic_data["timestamp"] = pd.to_datetime(
            historic_data["timestamp"], unit="s"
        )
        historic_data = historic_data[["open", "high", "low", "close", "volume"]]

        return historic_data.values

    def get_account_balance(self, account_id: str):
        """Retrieves the account balance for a given account_id"""

        account_details = self.private_client.get_account(account_id)
        return float(account_details["balance"])

    def predict(
        self, open_: float, high_: float, low_: float, close_: float, eth_volume_: float
    ):
        """Uses self.model to predict the close price 1-hour from now."""

        batch = [open_, high_, low_, close_, eth_volume_]
        model_prediction = self.model(batch)
        return model_prediction

    def place_buy_order(self, amount: float):
        """
        Checks to see if the amount to buy is greater than USD funds
        available, if so amount is set to the USD funds. Places a buy
        order.
        """
        
        usd_balance = self.get_account_balance(self.usd_wallet)

        if amount > usd_balance:
            amount = usd_balance

        buy_order_response = self.private_client.place_market_order(
            product_id=self.asset,
            side="buy",
            funds=str(amount)
        )
        return buy_order_response

    def place_sell_order(self, amount: float):
        """
        Checks to see if the amount to sell is greater than asset funds
        available, if so amount is set to the asset funds. Places a sell
        order.
        """
        
        asset_balance = self.get_account_balance(self.asset_wallet)

        if amount > asset_balance:
            amount = asset_balance

        sell_order_response = self.private_client.place_market_order(
            product_id=self.asset,
            side="sell",
            funds=str(amount)
        )
        return sell_order_response
