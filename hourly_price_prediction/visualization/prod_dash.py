import sys
sys.path.insert(0, "..")

import json
import os
import boto3
from glob import glob
from pathlib import Path

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
project_dir = Path(__file__).resolve().parents[2]

s3_client = boto3.client('s3')

app.layout = html.Div(
    [
        html.Div([html.H1("Algorithmic Trading Performance")]),
        html.Div(
            [
                html.Div(
                    [
                        html.H2("Model Name")
                    ],
                    className="col-md-12 col-sm-12",
                ),
                html.Div(
                    [dcc.Graph(id="prod-orders")], className="col-md-8 col-sm-12"
                ),
            ],
            className="row",
        ),
    ],
    className="container",
)

@app.callback(
    Output("prod-orders", "figure"),
)
def total_assets(model_dropdown):
    _, model_name = os.path.split(model_dropdown)
    base_model_path = os.path.join(
        project_dir, "data", "model_results", model_name)

    analyzer = PerformanceAnalyzer(
        path_to_model_metrics=os.path.join(
            base_model_path, "model_metrics.csv"),
        path_to_trading_history=os.path.join(
            base_model_path, "trading_history.csv"),
    )

    percentage_assets_html = analyzer.generate_line_plot(
        y_array=analyzer.trading_history.total_assets.values
        / analyzer.trading_history.total_assets.values[0],
        x_axis_title="Hours",
        y_axis_title="% Difference",
        graph_title="% Change by Hour",
        y_axis_unit=",.3%",
    )

    return percentage_assets_html

