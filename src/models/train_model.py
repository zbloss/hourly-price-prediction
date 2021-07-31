import os
import time
import joblib
import logging
import argparse
from numpy import percentile
import pandas as pd
from pathlib import Path

from sklearn.utils import validation
from utils import (
    get_model_class,
    train_test_val_split,
    training_pipeline,
    strategy_simulation
)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    project_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="CLI for training a machine learning model."
    )
    parser.add_argument(
        "--model_class",
        default="linearregressor",
        required=False,
        help="The model class object you would like to train",
        type=str,
    )
    parser.add_argument(
        "--csv_file",
        default=os.path.join(project_dir, "data", "processed", "processed_data.csv"),
        required=False,
        help="Path to the csv file you wish to use for training",
        type=str,
    )
    parser.add_argument(
        "--target_variable",
        default="NextClose",
        required=False,
        help="The column from the csv file that should be trained as the target variable.",
        type=str,
    )
    parser.add_argument(
        "--validation_percentage",
        default=0.2,
        required=False,
        help="The percentage of data you wish to reserve for validation.",
        type=float,
    )
    parser.add_argument(
        "--test_period_in_days",
        default=14,
        required=False,
        help="The number of sequential days you wish to holdout for final testing purposes.",
        type=int,
    )
    parser.add_argument(
        "--directory_to_save_models_in",
        default=os.path.join(project_dir, 'models'),
        required=False,
        help="The directory you want to save model artifacts into.",
        type=str,
    )
    parser.add_argument(
        "--directory_to_save_training_results_in",
        default=os.path.join(project_dir, 'data', 'model_results'),
        required=False,
        help="The directory you want to save training artifacts into.",
        type=str,
    )
    parser.add_argument(
        "--do_not_save_artifacts",
        action='store_true',
        help="Use this flag when you want to run the training pipeline without saving any artifacts."
    )

    command_line_arguments, unknown_command_line_arguments = parser.parse_known_args()
    model_class = str(command_line_arguments.model_class).lower()
    model_object = get_model_class(model_class)

    assert os.path.isfile(
        command_line_arguments.csv_file
    ), f"CSV File passed does not exist: {command_line_arguments.csv_file}"
    dataset = pd.read_csv(command_line_arguments.csv_file)
    dataset.columns = [column.lower() for column in dataset.columns]

    target_variable = str(command_line_arguments.target_variable).lower()
    assert (
        target_variable in dataset.columns
    ), f"Target variable passed (--target_variable {target_variable}) is not in the dataset (dataset.columns {dataset.columns})"

    train_features, train_targets, validation_features, validation_targets, test_features, test_targets = train_test_val_split(
        dataset,
        test_period_in_days=command_line_arguments.test_period_in_days,
        validation_percentage=command_line_arguments.validation_percentage,
        target_variable=target_variable,
    )

    model = model_object()
    train_metrics, validation_metrics, test_metrics = training_pipeline(
        model, 
        train_features, 
        train_targets, 
        validation_features,
        validation_targets,
        test_features,
        test_targets
    )

    trading_history, percentage_gain_lost = strategy_simulation(model, test_features, validation_metrics)
    logging.info(f'Total Gain/Loss after testing: {round(percentage_gain_lost*100, 5)}%')

    base_model_name = '{}-{}'.format(model_class, time.strftime('%Y%m%dT%H%M%S'))


    model_directories = [
        command_line_arguments.directory_to_save_models_in, 
        command_line_arguments.directory_to_save_training_results_in,
        os.path.join(command_line_arguments.directory_to_save_training_results_in, base_model_name)
    ]
    for directory in model_directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
    trading_history.to_csv(
        os.path.join(
            command_line_arguments.directory_to_save_training_results_in, 
            base_model_name, 
            'trading_history.csv'
        ),
        index=None
    )
    logging.info('Trading History Saved')

    pd.DataFrame([train_metrics, validation_metrics, test_metrics]).to_csv(
        os.path.join(
            command_line_arguments.directory_to_save_training_results_in, 
            base_model_name, 
            'model_metrics.csv'
        ),
        index=None
    )
    logging.info('Model Metrics Saved')

    if not command_line_arguments.do_not_save_artifacts:


        model_artifact = os.path.join(
            command_line_arguments.directory_to_save_models_in, 
            f'{base_model_name}.joblib'
        )
        joblib.dump(model, model_artifact)
        logging.info(f'Model Artifact saved: {model_artifact}')

