import json
import os
import sys
sys.path.insert(0, "..")
from glob import glob
from pathlib import Path

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from plotly.io import to_html
from hourly_price_prediction.models.performance_analyzer import PerformanceAnalyzer
import pandas as pd


external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
project_dir = Path(__file__).resolve().parents[2]

available_model_paths = glob(f"{project_dir}/data/model_results/*")
available_models = [os.path.split(apm)[1] for apm in available_model_paths]
zipped_models = dict(zip(available_model_paths, available_models))

analyzer = PerformanceAnalyzer(
    path_to_model_metrics=os.path.join(available_model_paths[0], "model_metrics.csv"),
    path_to_trading_history=os.path.join(available_model_paths[0], "trading_history.csv"),
)
descriptive_statistics = pd.DataFrame(analyzer.trading_history_descriptive_statistics).T

all_model_metrics = pd.DataFrame()
for model_path in available_model_paths:
    metrics = pd.read_csv(os.path.join(model_path, 'model_metrics.csv'))
    _, model_name = os.path.split(model_path)
    metrics['model'] = model_name
    all_model_metrics = pd.concat((all_model_metrics, metrics), ignore_index=True)
all_model_metrics.reset_index(inplace=True, drop=True)

app.layout = html.Div(
    [
        html.Div([
            html.Div([
                html.H1("Algorithmic Trading Performance"),
                html.Br(),
                html.Hr()
            ], className='col')
            
        ], className="row"),

        html.Div(
            [
                html.Div(
                    [html.H2("Model Name", id='model-name')],
                    className="col-md-8 col-sm-12",
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
                html.Div([html.Br(), html.Br(), html.Br()], className='col-sm-12')
            ],
            className="row",
        ),
        html.Div([
            html.Div([
                dcc.Graph(id='total-assets-graphic')
            ], className="col-sm-6"),
            html.Div([
                dcc.Graph(id='total-eth-graphic')
            ], className="col-sm-6"),
        ], className="row"),
        html.Div([
            dash_table.DataTable(
                id='descriptive-statistics-table',
                columns=[{'name': i, 'id': i} for i in sorted(descriptive_statistics.columns)],
                page_current=0,
                page_size=5,
                page_action='native',
                sort_action='native',
                column_selectable="single",
                row_selectable="single",
                sort_mode='multi',
                style_table={
                    'overflowX': 'scroll',
                    'maxHeight':'300px',
                    'height': 'auto'
                    },
                ),
        ], className="row"),
        html.Br(),
        html.Hr(),
        html.Br(),
        html.Div([
            dash_table.DataTable(
                id='model-error-train-table',
                columns=[{'name': i, 'id': i} for i in ['MAE', 'MSE', 'RMSE', 'R2']],
                page_current=0,
                page_size=5,
                page_action='native',
                sort_action='native',
                column_selectable="single",
                row_selectable="single",
                sort_mode='multi',
                style_table={
                    'overflowX': 'scroll',
                    'maxHeight':'300px',
                    'height': 'auto'
                    },
                ),
        ], className="row"),
        html.Div([
            dash_table.DataTable(
                id='model-error-val-table',
                columns=[{'name': i, 'id': i} for i in ['MAE', 'MSE', 'RMSE', 'R2']],
                page_current=0,
                page_size=5,
                page_action='native',
                sort_action='native',
                column_selectable="single",
                row_selectable="single",
                sort_mode='multi',
                style_table={
                    'overflowX': 'scroll',
                    'maxHeight':'300px',
                    'height': 'auto'
                    },
                ),
        ], className="row"),
        html.Div([
            dash_table.DataTable(
                id='model-error-test-table',
                columns=[{'name': i, 'id': i} for i in ['MAE', 'MSE', 'RMSE', 'R2']],
                page_current=0,
                page_size=5,
                page_action='native',
                sort_action='native',
                column_selectable="single",
                row_selectable="single",
                sort_mode='multi',
                style_table={
                    'overflowX': 'scroll',
                    'maxHeight':'300px',
                    'height': 'auto'
                    },
                ),
        ], className="row"),
        html.Div([
            html.Div([
                html.Div([dcc.Graph(id='kpi-total-assets')], className='col'),
                html.Div([dcc.Graph(id='kpi-annualized-std')], className='col'),
                html.Div([dcc.Graph(id='kpi-total-assets-max-vs-min')], className='col'),
            ], className="row"),
            html.Div([
                html.Div([dcc.Graph(id='kpi-total-buys')], className='col'),
                html.Div([dcc.Graph(id='kpi-total-sells')], className='col'),
                html.Div([dcc.Graph(id='kpi-total-do-nothings')], className='col'),
            ], className="row"),
        ]),

        html.Div([
            dash_table.DataTable(
                id='all-model-metrics-table',
                columns=[{'name': i, 'id': i} for i in all_model_metrics.columns],
                page_current=0,
                page_size=20, 
                filter_action='native',
                data=all_model_metrics.to_dict(orient='records'),
                page_action='native',
                sort_action='native',
                column_selectable="single",
                row_selectable="single",
                sort_mode='multi',
                style_table={
                    'overflowX': 'scroll',
                    'maxHeight':'300px',
                    'height': 'auto'
                    },
                ),
        ], className="row"),
    ],
    className="container",
)

@app.callback(
    Output("model-name", "children"),
    Input("model-dropdown", "value"),
)
def total_assets(model_dropdown):
    _, model_name = os.path.split(model_dropdown)
    
    return model_name

@app.callback(
    Output("total-assets-graphic", "figure"),
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

    percentage_assets_fig = analyzer.generate_line_plot(
        y_array=analyzer.trading_history.total_assets.values
        / analyzer.trading_history.total_assets.values[0],
        x_axis_title="Hours",
        y_axis_title="% Difference",
        graph_title="% Change by Hour",
        y_axis_unit=",.3%",
    )

    return percentage_assets_fig

@app.callback(
    Output("total-eth-graphic", "figure"),
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

    percentage_assets_fig = analyzer.generate_line_plot(
        y_array=analyzer.trading_history.asset_wallet_balance.values
        / analyzer.trading_history.asset_wallet_balance.values[0],
        x_axis_title="Hours",
        y_axis_title="ETH Wallet",
        graph_title="Change by Hour",
    )

    return percentage_assets_fig


@app.callback(
    dash.dependencies.Output('descriptive-statistics-table','data'),
    [dash.dependencies.Input('model-dropdown','value')]
)
def get_descriptive_statistics(model_dropdown):
    _, model_name = os.path.split(model_dropdown)
    base_model_path = os.path.join(
        project_dir, "data", "model_results", model_name)

    analyzer = PerformanceAnalyzer(
        path_to_model_metrics=os.path.join(
            base_model_path, "model_metrics.csv"),
        path_to_trading_history=os.path.join(
            base_model_path, "trading_history.csv"),
    )

    descriptive_statistics = analyzer.trading_history_descriptive_statistics

    return pd.DataFrame(descriptive_statistics).T.to_dict(orient='records')


@app.callback(
    Output("kpi-total-assets", "figure"),
    Output("kpi-annualized-std", "figure"),
    Output("kpi-total-assets-max-vs-min", "figure"),
    Output("kpi-total-buys", "figure"),
    Output("kpi-total-sells", "figure"),
    Output("kpi-total-do-nothings", "figure"),
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

    return plots

@app.callback(
    dash.dependencies.Output('model-error-train-table','data'),
    dash.dependencies.Output('model-error-val-table','data'),
    dash.dependencies.Output('model-error-test-table','data'),
    [dash.dependencies.Input('model-dropdown','value')]
)
def get_model_errors(model_dropdown):
    _, model_name = os.path.split(model_dropdown)
    base_model_path = os.path.join(
        project_dir, "data", "model_results", model_name)

    analyzer = PerformanceAnalyzer(
        path_to_model_metrics=os.path.join(base_model_path, "model_metrics.csv"),
        path_to_trading_history=os.path.join(base_model_path, "trading_history.csv"),
    )

    model_error_metrics = [
        {
            'MAE': analyzer.train_mean_absolute_error,
            'MSE': analyzer.train_mean_squared_error,
            'RMSE': analyzer.train_root_mean_squared_error,
            'R2': analyzer.train_r2
        },
        {
            'MAE': analyzer.val_mean_absolute_error,
            'MSE': analyzer.val_mean_squared_error,
            'RMSE': analyzer.val_root_mean_squared_error,
            'R2': analyzer.val_r2
        },
        {
            'MAE': analyzer.test_mean_absolute_error,
            'MSE': analyzer.test_mean_squared_error,
            'RMSE': analyzer.test_root_mean_squared_error,
            'R2': analyzer.test_r2
        },
    ]

    return [pd.DataFrame.from_dict(mem, orient='index').T.to_dict(orient='records') for mem in model_error_metrics]


if __name__ == '__main__':
    port = os.getenv('PORT')
    host = os.getenv('HOST')

    if port == '' or port == None:
        port = '5000'
    
    if host == '' or host == None:
        host = '0.0.0.0'

    app.run_server(host=host, port=port, debug=True)
