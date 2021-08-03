import logging
import os

import hydra
import numpy as np
import pandas as pd
import plotly
from omegaconf import DictConfig
from glob import glob

from performance_analyzer import PerformanceAnalyzer

def performance_pipeline(cfg: DictConfig):
    path_to_model_metrics = os.path.join(cfg.data.base_directory, cfg.data.model_name, 'model_metrics.csv')
    path_to_trading_history = os.path.join(cfg.data.base_directory, cfg.data.model_name, 'trading_history.csv')

    for filepath in [path_to_model_metrics, path_to_trading_history]:
        assert os.path.isfile(filepath), f'File does not exist: {filepath}'

    analyzer = PerformanceAnalyzer(
        path_to_model_metrics=path_to_model_metrics, 
        path_to_trading_history=path_to_trading_history
    )
    analysis_directory = os.path.join(cfg.data.output_directory, cfg.data.model_name)
    figures_directory = os.path.join(cfg.data.output_directory, 'figures', cfg.data.model_name)
    for directory in [analysis_directory, figures_directory]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    percentage_assets_html = analyzer.generate_line_plot(
        y_array = analyzer.trading_history.total_assets.values / analyzer.trading_history.total_assets.values[0], 
        x_axis_title = 'Hours', 
        y_axis_title = '% Difference', 
        graph_title = '% Change by Hour',
        y_axis_unit=',.3%'
    )

    percentage_asset_card = analyzer.generate_card(
        percentage_assets_html,
        "Total Assets [% Change]",
    )

    current_total_assets = analyzer.trading_history.total_assets.values[-1]
    initial_total_assets = analyzer.trading_history.total_assets.values[0]

    current_values = [current_total_assets, analyzer.annualized_std(), analyzer.asset_max, analyzer.total_buys, analyzer.total_sells, analyzer.total_do_nothing]
    initial_values = [initial_total_assets, analyzer.annualized_std(), analyzer.asset_min, analyzer.total_buys, analyzer.total_sells, analyzer.total_do_nothing]
    texts = ['Total Assets', 'Annualized STD', 'Total Asset Max vs Min', 'Total Buys', 'Total Sells', 'Total Do Nothings']
    units = ['$', '', '$', '', '', '']
    kpi_chart = analyzer.generate_kpi_plot(
        current_values=current_values, 
        initial_values=initial_values, 
        texts=texts,
        units=units
    )
    kpi_card = analyzer.generate_card(kpi_chart, 'KPIs')
    
    body_style =  f"margin:0 100; background:{cfg.html.background_color};"
    html = '''<html>
        <head>
            <link rel="stylesheet" href="{stylesheet}">
            <style>body{body_style}</style>
            <script src="{script}" integrity="{integrity}" crossorigin="{crossorigin}"></script>
        </head>
        <body>
            <div class="container">
                <div class="row">
                    <div class="col-sm-12">
                        <h1>{text}</h1>
                    </div>
                </div>

                <div class="row"><div class="col-sm-12">{kpi_card}</div></div>
                <div class="row"><div class="col-sm-12">{percentage_asset_card}</div></div>


            </div>
        </body>
    </html>'''.format(
        stylesheet=cfg.html.stylesheet, 
        script=cfg.html.js.script,
        integrity=cfg.html.js.integrity,
        crossorigin=cfg.html.js.crossorigin,
        body_style=body_style, 
        text=cfg.data.model_name,
        percentage_asset_card=percentage_asset_card,
        kpi_card=kpi_card
    )
    analysis_file = os.path.join(analysis_directory, 'analysis.html')
    with open(analysis_file, 'w') as afile:
        afile.write(html)
        afile.close()

    logging.info(f'Analysis written to {analysis_file}')


@hydra.main(config_path="../../configs/analyze", config_name="analyze_single")
def analyze_performance(cfg: DictConfig):
    
    if cfg.data.model_name == 'run_all':
        models = glob('../../../data/model_results/*', )

        for model in models:
            cfg.data.model_name = model.split('/')[-1]
            performance_pipeline(cfg)
    else:
        performance_pipeline(cfg)

    
if __name__ == '__main__':
    analyze_performance()

    

