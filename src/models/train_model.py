import hydra
from omegaconf import DictConfig, OmegaConf
import os
import time
import joblib
import logging
import pandas as pd
from utils import (
    get_model_class,
    train_test_val_split,
    training_pipeline,
    strategy_simulation
)



@hydra.main(config_path="../../configs", config_name="linear_config")
def train_model(cfg: DictConfig) -> None:
    
    print(OmegaConf.to_yaml(cfg))

    model_object = get_model_class(cfg.model.model_class)

    assert os.path.isfile(
        cfg.data.csv_file
    ), f"CSV File passed does not exist: {cfg.data.csv_file}"
    dataset = pd.read_csv(cfg.data.csv_file)
    dataset.columns = [column.lower() for column in dataset.columns]

    assert (
        cfg.model.target_variable in dataset.columns
    ), f"Target variable passed (--target_variable {cfg.model.target_variable}) is not in the dataset (dataset.columns {dataset.columns})"

    train_features, train_targets, validation_features, validation_targets, test_features, test_targets = train_test_val_split(
        dataset,
        test_period_in_days=cfg.model.test_period_in_days,
        validation_percentage=cfg.model.validation_percentage,
        target_variable=cfg.model.target_variable,
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

    base_model_name = '{}-{}'.format(cfg.model.model_class, time.strftime('%Y%m%dT%H%M%S'))

    model_directories = [
        cfg.data.directory_to_save_models_in, 
        cfg.data.directory_to_save_training_results_in,
        os.path.join(cfg.data.directory_to_save_training_results_in, base_model_name)
    ]
    for directory in model_directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
    trading_history.to_csv(
        os.path.join(
            cfg.data.directory_to_save_training_results_in, 
            base_model_name, 
            'trading_history.csv'
        ),
        index=None
    )
    logging.info('Trading History Saved')

    pd.DataFrame([train_metrics, validation_metrics, test_metrics]).to_csv(
        os.path.join(
            cfg.data.directory_to_save_training_results_in, 
            base_model_name, 
            'model_metrics.csv'
        ),
        index=None
    )
    logging.info('Model Metrics Saved')

    if cfg.model.save_artifacts:


        model_artifact = os.path.join(
            cfg.data.directory_to_save_models_in, 
            f'{base_model_name}.joblib'
        )
        joblib.dump(model, model_artifact)
        logging.info(f'Model Artifact saved: {model_artifact}')


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    train_model()
