import logging
import os
import hydra
from omegaconf import DictConfig

import pandas as pd
import requests


def download_csv_file(url_path_to_csv_file: str) -> bytes:
    """
    Given a url that links to a CSV file, this function will download that
    file and return it as a DataFrame.
    """
    logger = logging.getLogger(__name__)

    if not url_path_to_csv_file.startswith("http"):
        url_path_to_csv_file = f"http://{url_path_to_csv_file}"

    response = requests.get(url_path_to_csv_file, verify=False)
    csv_content = response.content
    logger.info(f"Downloaded CSV data from: {url_path_to_csv_file}")

    return csv_content


def process_raw_data(raw_data_filepath: str, processed_data_filepath: str) -> None:
    """
    Runs data processing scripts to turn raw data from (../raw) into
    cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)

    raw_data = pd.read_csv(raw_data_filepath, skiprows=1)

    for column in ["Volume USD", "unix", "symbol"]:
        try:
            raw_data.drop(column, axis=1, inplace=True)
        except IndexError as e:
            logger.warn(f"Unable to drop column from the raw dataframe: {column} | {e}")
            pass

    raw_data = raw_data.rename(
        {"date": "TimeStamp", "Volume ETH": "Volume_ETH", "close": "CurrentClose"},
        axis=1,
    )
    raw_data["TimeStamp"] = pd.to_datetime(raw_data["TimeStamp"])
    target = raw_data["CurrentClose"].shift(-1)
    raw_data["NextClose"] = target
    raw_data.dropna(inplace=True, axis=0)
    raw_data.set_index("TimeStamp", inplace=True)
    raw_data.to_csv(processed_data_filepath, index=None)
    return None


@hydra.main(config_path="../../configs/data", config_name="data")
def main(cfg: DictConfig):

    csv_data = download_csv_file(url_path_to_csv_file=cfg.web_url)
    logging.info(f"csv_data type: {type(csv_data)}")

    required_directories = [
        cfg.raw_file_directory,
        cfg.processed_file_directory,
    ]
    for directory in required_directories:
        if not os.path.isdir(directory):
            os.makedirs(directory)

    raw_data_filepath = os.path.join(
        cfg.raw_file_directory, "raw_data.csv"
    )
    processed_data_filepath = os.path.join(
        cfg.processed_file_directory, "processed_data.csv"
    )
    with open(raw_data_filepath, "wb") as csv_file:
        csv_file.write(csv_data)
        csv_file.close()

    process_raw_data(
        raw_data_filepath=raw_data_filepath,
        processed_data_filepath=processed_data_filepath,
    )
    logging.info(f"Raw Data File: {raw_data_filepath}")
    logging.info(f"Processed Data File: {processed_data_filepath}")


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
    logging.info("Done!")
