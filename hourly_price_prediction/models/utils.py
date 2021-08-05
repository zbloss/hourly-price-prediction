import boto3
import logging
from math import sqrt

import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def get_model_class(model_class: str) -> BaseEstimator:
    """
    Helper function that abstracts away the ugly-mess of determining
    which Machine Learning Model class to import

    :param model_class: (str) a string representing which class to import.
    :returns: the base model class.
    """
    logger = logging.getLogger(__name__)
    model_object = None
    if model_class == "LinearRegressor".lower():
        from sklearn.linear_model import LinearRegression as model_object

    elif model_class == "GradientBoostingRegressor".lower():
        from sklearn.ensemble import GradientBoostingRegressor as model_object

    elif model_class == "RandomForestRegressor".lower():
        from sklearn.ensemble import RandomForestRegressor as model_object

    elif model_class == "DecisionTreeRegressor".lower():
        from sklearn.tree import DecisionTreeRegressor as model_object

    elif model_class == "KNeighborsRegressor".lower():
        from sklearn.neighbors import KNeighborsRegressor as model_object

    elif model_class == "MLPRegressor".lower():
        from sklearn.neural_network import MLPRegressor as model_object

    elif model_class == "Ridge".lower():
        from sklearn.linear_model import Ridge as model_object

    elif model_class == "ElasticNet".lower():
        from sklearn.linear_model import ElasticNet as model_object

    elif model_class == "BayesianRidge".lower():
        from sklearn.linear_model import BayesianRidge as model_object

    elif model_class == "HuberRegressor".lower():
        from sklearn.linear_model import HuberRegressor as model_object

    else:
        raise AssertionError("Invalid Model Class passed to --model_class object")
    logger.info(f'Using {model_object}')
    return model_object


def score_metrics(actual_values: list, model_predictions: list, mode: str) -> dict:
    """
    Given a set of true values (actual_values) and model predicted values (model_predictions)
    this function will return a dictionary with various regression metrics.
    """

    mse = mean_squared_error(actual_values, model_predictions)
    return {
        "mode": str(mode).lower(),
        "mae": mean_absolute_error(actual_values, model_predictions),
        "mse": mean_squared_error(actual_values, model_predictions),
        "rmse": sqrt(mse),
        "r2": r2_score(actual_values, model_predictions),
    }


def feature_target_split(dataset: pd.DataFrame, target_variable: str) -> tuple:
    """
    Splits `dataset` into a feature and target dataframe on the `target_variable`
    attribute.

    :returns: tuple(features, targets)
    """

    features = dataset.drop(target_variable, axis=1)
    targets = dataset[target_variable]
    return (features, targets)


def train_test_val_split(
    dataset: pd.DataFrame,
    test_period_in_days: int,
    validation_percentage: float,
    target_variable: str,
) -> tuple:
    """
    Splits the `dataset` into training, testing, and validation splits by first
    extracting the final testing set by converting `test_period_in_days` into
    hours and then grabbing that many rows from the end of the `dataset`. Then
    it utilizes the scikit-learn `train_test_split` function to split the training
    data into training and validation sets according to the `validation_percentage`
    size.

    :returns: tuple(train_features, train_targets, validation_features, validation_targets, test_features, test_targets)
    """

    test_period_in_hours = 24 * int(test_period_in_days)
    number_of_hours_in_dataset = dataset.count()[0]
    assert (
        test_period_in_hours < number_of_hours_in_dataset
    ), f"Final testing period exceeds dataset size (test size: {test_period_in_hours} | dataset size: {number_of_hours_in_dataset})"

    test_dataset = dataset.iloc[-test_period_in_hours:]
    test_features, test_targets = feature_target_split(test_dataset, target_variable)

    dataset = dataset.iloc[:-test_period_in_hours]
    features, targets = feature_target_split(dataset, target_variable)
    (
        train_features,
        validation_features,
        train_targets,
        validation_targets,
    ) = train_test_split(
        features, targets, test_size=validation_percentage, random_state=43
    )
    return (
        train_features,
        train_targets,
        validation_features,
        validation_targets,
        test_features,
        test_targets,
    )

def training_pipeline(
    model, 
    train_features, 
    train_targets, 
    validation_features, 
    validation_targets, 
    test_features, 
    test_targets
) -> list:
    logger = logging.getLogger(__name__)
    model.fit(train_features, train_targets)
    logger.info('Model Trained')

    train_predictions = model.predict(train_features)
    validation_predictions = model.predict(validation_features)
    test_predictions = model.predict(test_features)
    logger.info('Predictions Made')

    train_metrics = score_metrics(train_targets, train_predictions, "train")
    validation_metrics = score_metrics(validation_targets, validation_predictions, "val")
    test_metrics = score_metrics(test_targets, test_predictions, "test")
    logger.info('Metrics Generated')

    return [train_metrics, validation_metrics, test_metrics]

def strategy_simulation(
    model: BaseEstimator,
    test_dataset: pd.DataFrame, 
    validation_metrics: dict,
    initial_money: int = 100,
    percent_of_total_money_to_move: float = 0.10,
) -> tuple:
    """
    This function tests a simple trading strategy given a model, dataset, and 
    the model's performance dictionary on the validation dataset.
    """

    asset_wallet_balance = 0.0
    total_assets = 0.0
    amount_of_asset_to_exchange = 0.0
    amount_of_usd_to_exchange = 0.0

    trading_history = []
    for step, (_, series) in enumerate(test_dataset.iterrows()):
        
        if step == 0:
            total_money = initial_money
        
        current_close = series['currentclose']
        model_prediction = model.predict(series.values.reshape(1, -1))

        action = 'do_nothing'
        if abs(model_prediction - current_close) > (validation_metrics['mae'] / 3):
            if model_prediction - current_close > 0:
                action = 'buy'
            else:
                action = 'sell'
        
        amount_of_usd_to_exchange = percent_of_total_money_to_move * total_money
        amount_of_asset_to_exchange = amount_of_usd_to_exchange / current_close
        
        if total_money <= 0:
            break
        else:
            
            if action == 'sell':
                if amount_of_asset_to_exchange > asset_wallet_balance:
                    amount_of_asset_to_exchange = asset_wallet_balance

                total_money += amount_of_asset_to_exchange * current_close
                asset_wallet_balance -= amount_of_asset_to_exchange
                assert asset_wallet_balance >= 0, f'asset_wallet_balance is negative: {asset_wallet_balance}'

            elif action == 'buy':
                if amount_of_usd_to_exchange > total_money:
                    amount_of_usd_to_exchange = total_money

                total_money -= amount_of_usd_to_exchange
                asset_wallet_balance += amount_of_asset_to_exchange

            else:
                pass
            
            total_assets = asset_wallet_balance * current_close + total_money
        
            actions_this_turn = {
                'action': action,
                'amount_of_asset_to_exchange': amount_of_asset_to_exchange,
                'amount_of_usd_to_exchange': amount_of_usd_to_exchange,
                'asset_wallet_balance': asset_wallet_balance,
                'total_money': total_money,
                'total_assets': total_assets
            }
            trading_history.append(actions_this_turn)
            
    trading_history = pd.DataFrame(trading_history)

    final_assets = trading_history['total_assets'].iloc[-1]
    difference_between_final_assets_and_initial_money = final_assets - initial_money
    percentage_gain_lost = difference_between_final_assets_and_initial_money / initial_money

    return (trading_history, percentage_gain_lost)

def download_from_s3(bucket: str, key: str, filename: str, region_name: str = 'us-east-2'):
    """
    Given a Bucket and Key, this function will download the file
    and store it at filename.
    
    """

    s3_client = boto3.client('s3', region_name=region_name)
    s3_response = s3_client.download_file(bucket, key, filename)
    return s3_response


def write_to_s3(bucket: str, key: str, filename: str, region_name: str = 'us-east-2'):
    """
    Given a Bucket and Key, this function will write the file
    and to the S3 bucket+key location.
    
    """

    s3_client = boto3.client('s3', region_name='us-east-2')
    s3_response = s3_client.upload_file(filename, bucket, key)
    return s3_response
