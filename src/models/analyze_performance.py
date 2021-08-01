import os
import logging
import argparse
from pathlib import Path
import pandas as pd
from performance_analyzer import PerformanceAnalyzer


if __name__ == '__main__':
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    project_dir = Path(__file__).resolve().parents[2]

    parser = argparse.ArgumentParser(description='CLI for analyzing the performance of a model')
    parser.add_argument(
        '--path_to_model_metrics', 
        type=str, 
        required=True, 
        help='path to a csv containing model train/val/test metrics.'
    )
    parser.add_argument(
        '--path_to_trading_history', 
        type=str, 
        required=True, 
        help='path to a csv containing the generated trading history from the final round of model testing.'
    )

    command_line_arguments, unknown_command_line_arguments = parser.parse_known_args()
    if len(unknown_command_line_arguments) > 0:
        logging.info(f'Unknown Command Line Arguments passed: {unknown_command_line_arguments}')

    for filepath in [command_line_arguments.path_to_model_metrics, command_line_arguments.path_to_trading_history]:
        assertion_message = f'File passed to the performance analyzer does not exist: {filepath}'
        assert os.path.isfile(filepath) == True, assertion_message

    analyzer = PerformanceAnalyzer(
        path_to_model_metrics=command_line_arguments.path_to_model_metrics, 
        path_to_trading_history=command_line_arguments.path_to_trading_history
    )
    logging.info('PerformanceAnalyzer Initiated')

    logging.info(f'Train MAE: {analyzer.train_mean_absolute_error}')
    logging.info(f'Asset Max: {analyzer.asset_max}')
    logging.info(f'Total Assets Annualized STD: {analyzer.annualized_std()}')

    

