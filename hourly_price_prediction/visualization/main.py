import json
import os
import sys
sys.path.insert(0, "..")
from glob import glob
from pathlib import Path

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from hourly_price_prediction.models.performance_analyzer import PerformanceAnalyzer


external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
project_dir = Path(__file__).resolve().parents[2]

available_model_paths = glob(f"{project_dir}/data/model_results/*")
available_models = [os.path.split(apm)[1] for apm in available_model_paths]
zipped_models = dict(zip(available_model_paths, available_models))

app.layout = html.Div(
    [
        html.Div([html.H1("Algorithmic Trading Performance")]),
        html.Div(
            [
                html.Div(
                    [
                        html.H2("Model Name"),
                        html.Div(id='kpi-graphic') 
                        #dcc.Graph("kpi-graphic")
                    ],
                    className="col-md-12 col-sm-12",
                ),
                html.Div(
                    [dcc.Graph(id="asset-graphic")], className="col-md-8 col-sm-12"
                ),
                html.Div(
                    [
                        dcc.Dropdown(
                            id="model-dropdown",
                            options=[
                                {"label": model, "value": paths}
                                for paths, model in zipped_models.items()
                            ],
                            value=available_models[0],
                        ),
                    ],
                    className="col-md-4 col-sm-12",
                ),
            ],
            className="row",
        ),
    ],
    className="container",
)


@app.callback(
    Output("asset-graphic", "figure"),
    Input("model-dropdown", "value"),
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


@app.callback(
    Output("kpi-graphic", "children"),
    Input("model-dropdown", "value"),
)
def kpi_graph(model_dropdown):

    _, model_name = os.path.split(model_dropdown)
    base_model_path = os.path.join(
        project_dir, "data", "model_results", model_name)

    analyzer = PerformanceAnalyzer(
        path_to_model_metrics=os.path.join(
            base_model_path, "model_metrics.csv"),
        path_to_trading_history=os.path.join(
            base_model_path, "trading_history.csv"),
    )

    current_total_assets = analyzer.trading_history.total_assets.values[-1]
    initial_total_assets = analyzer.trading_history.total_assets.values[0]

    current_values = [
        current_total_assets,
        analyzer.annualized_std(),
        analyzer.asset_max,
        analyzer.total_buys,
        analyzer.total_sells,
        analyzer.total_do_nothing,
    ]
    initial_values = [
        initial_total_assets,
        analyzer.annualized_std(),
        analyzer.asset_min,
        analyzer.total_buys,
        analyzer.total_sells,
        analyzer.total_do_nothing,
    ]
    texts = [
        "Total Assets",
        "Annualized STD",
        "Total Asset Max vs Min",
        "Total Buys",
        "Total Sells",
        "Total Do Nothings",
    ]
    units = ["$", "", "$", "", "", ""]

    plots = []
    for idx, _ in enumerate(current_values):
        current_value = current_values[idx]
        initial_value = initial_values[idx]
        text = texts[idx]
        unit = units[idx]
        kpi_plot = analyzer._generate_kpi_plot(
            current_value, 
            initial_value, 
            text, 
            subtitle='', 
            unit=unit
        )
        plots.append(kpi_plot)

    return html.Div([html.Div(plot, className='col') for plot in plots])
    # kpi_chart = analyzer.generate_kpi_plot(
    #     current_values=current_values,
    #     initial_values=initial_values,
    #     texts=texts,
    #     units=units,
    # )

    # return kpi_chart


if __name__ == "__main__":
    app.run_server(debug=True)
