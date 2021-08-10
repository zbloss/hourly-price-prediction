import sys
sys.path.insert(0, "..")

import json
import os
import boto3
import pandas as pd
from glob import glob
from pathlib import Path
import plotly.graph_objects as go

import dash
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
# for obj in bucket.objects.filter(Prefix='trading_history/'):
#     object_key = obj.key
#     filepath, filename = os.path.split(object_key)

#     if not os.path.isdir(os.path.join(project_dir, 'data', 'trading_history', filename)):
#         bucket.download_file(
#             object_key,
#             os.path.join(project_dir, 'data', 'trading_history', filename)
#         )

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

    fig = go.Figure(layout=layout)
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], 
            y=df['total_assets'], 
            mode="lines", 
            name='total_assets'
        ),
    )

    fig.update_layout(yaxis_tickformat='$')

    return fig

@app.callback(
    Output("eth-price", "figure"),
    Input(component_id='my-input', component_property='value')
)
def total_assets(value):

    layout = go.Layout(
        title=go.layout.Title(text='Price of ETH [In USD]'),
        xaxis=go.layout.XAxis(title='DateTime'),
        yaxis=go.layout.YAxis(title='Price of ETH'),
    )

    fig = go.Figure(layout=layout)
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], 
            y=df['close'], 
            mode="lines", 
            name='eth_price'
        ),
    )

    fig.update_layout(yaxis_tickformat='$')

    return fig


if __name__ == '__main__':
    port = os.getenv('PORT')
    host = os.getenv('HOST')

    if port == '' or port == None:
        port = '5000'
    
    if host == '' or host == None:
        host = '0.0.0.0'

    app.run_server(host=host, port=port, debug=True)