import sys
sys.path.insert(0, "..")

import json
import os
import boto3
import pandas as pd
from glob import glob
from pathlib import Path
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from hourly_price_prediction.models.utils import download_from_s3

external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
project_dir = Path(__file__).resolve().parents[2]
bucket = 'hourly-price-prediction'
s3_resource = boto3.resource('s3')
bucket = s3_resource.Bucket(bucket)
for obj in bucket.objects.filter(Prefix='trading_history/'):
    object_key = obj.key
    filepath, filename = os.path.split(object_key)

    if not os.path.isdir(os.path.join(project_dir, 'data', 'trading_history', filename)):
        bucket.download_file(
            object_key,
            os.path.join(project_dir, 'data', 'trading_history', filename)
        )

data = []
for json_filepath in glob(os.path.join(project_dir, 'data', 'trading_history', '*.json')):
    with open(json_filepath, 'r') as jfile:
        data.append(json.loads(jfile.read()))
        jfile.close()

df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
df['total_assets'] = df['close'] * df['asset_wallet'] + df['usd_wallet']
df.sort_values(by='timestamp', ascending=True, inplace=True)

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
                    [dcc.Graph(id="prod-orders")], className="col-sm-12"
                ),
                html.Div(
                    [dcc.Graph(id='eth-price')], className="col-sm-12"
                ),
                html.Div(["Input: ", dcc.Input(id='my-input', value='initial value', type='text')]),
            ],
            className="row",
        ),
        html.Div([
            html.Div([
                dash_table.DataTable(
                    id='datatable-interactivity',
                    columns = [
                        {"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns
                    ],
                    data=df.to_dict(orient='records'),
                    editable=True,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="single",
                    row_selectable="multi",
                    row_deletable=False,
                    selected_columns=[],
                    selected_rows=[],
                    page_action="native",
                    page_current=0,
                    page_size=10,
                    style_cell={
                        'whiteSpace': 'normal',
                        'height': 'auto',
                    }
                )
            ], className="col-sm-12")
        ], className="row")
    ],
    className="container",
)

@app.callback(
    Output("prod-orders", "figure"),
    Input(component_id='my-input', component_property='value')
)
def total_assets(value):

    layout = go.Layout(
        title=go.layout.Title(text='Ethereum Trading'),
        xaxis=go.layout.XAxis(title='DateTime'),
        yaxis=go.layout.YAxis(title='Asset Values [In USD]'),
    )
    marker_color = []
    texts = []
    for idx, action in enumerate(df['action'].values):
        if action == 'buy':
            color = 'azure'
        elif action == 'sell':
            color = 'red'
        else:
            color = 'black'

        text = f'Action: {action}'
        texts.append(text)
        marker_color.append(color)
    fig = go.Figure(layout=layout)
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], 
            y=df['total_assets'], 
            mode="lines+markers", 
            name='total_assets',
            marker_color=marker_color, text=texts
        ),
    )
    fig.update_layout(yaxis_tickformat='$')

    return fig

@app.callback(
    Output("eth-price", "figure"),
    Input(component_id='my-input', component_property='value')
)
def eth_pricing(value):

    layout = go.Layout(
        title=go.layout.Title(text='Price of ETH [In USD]'),
        xaxis=go.layout.XAxis(title='DateTime'),
        yaxis=go.layout.YAxis(title='Price of ETH'),
    )
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=['Price of ETH [In USD]', 'ETH Volume']
    )

    # include candlestick with rangeselector
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'], 
            high=df['high'],
            low=df['low'], 
            close=df['close']
            ), secondary_y=True)

    # include a go.Bar trace for volumes
    fig.add_trace(
        go.Bar(
            x=df['timestamp'], 
            y=df['volume']
        ), secondary_y=False)

    fig.layout.yaxis2.showgrid=False
    

    return fig

@app.callback(
    Output('datatable-interactivity', 'style_data_conditional'),
    Input('datatable-interactivity', 'selected_columns')
)
def update_styles(selected_columns):
    return [{
        'if': { 'column_id': i },
        'background_color': '#D2F3FF'
    } for i in selected_columns]




if __name__ == '__main__':
    port = os.getenv('PORT')
    host = os.getenv('HOST')

    if port == '' or port == None:
        port = '5000'
    
    if host == '' or host == None:
        host = '0.0.0.0'

    app.run_server(host=host, port=port, debug=True)