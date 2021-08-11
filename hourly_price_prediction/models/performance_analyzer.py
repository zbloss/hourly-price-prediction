from typing import List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html
from plotly.subplots import make_subplots


class PerformanceAnalyzer(object):
    def __init__(self, path_to_model_metrics: str, path_to_trading_history: str):

        self.model_metrics = pd.read_csv(path_to_model_metrics)
        self.trading_history = pd.read_csv(path_to_trading_history)

        self.trading_history_descriptive_statistics = self.trading_history[
            "total_assets"
        ].describe()

    @property
    def train_mean_absolute_error(self):
        return self.model_metrics[self.model_metrics["mode"] == "train"]["mae"].values[
            0
        ]

    @property
    def val_mean_absolute_error(self):
        return self.model_metrics[self.model_metrics["mode"] == "val"]["mae"].values[0]

    @property
    def test_mean_absolute_error(self):
        return self.model_metrics[self.model_metrics["mode"] == "test"]["mae"].values[0]

    @property
    def train_mean_squared_error(self):
        return self.model_metrics[self.model_metrics["mode"] == "train"]["mse"].values[
            0
        ]

    @property
    def val_mean_squared_error(self):
        return self.model_metrics[self.model_metrics["mode"] == "val"]["mse"].values[0]

    @property
    def test_mean_squared_error(self):
        return self.model_metrics[self.model_metrics["mode"] == "test"]["mse"].values[0]

    @property
    def train_root_mean_squared_error(self):
        return self.model_metrics[self.model_metrics["mode"] == "train"]["rmse"].values[
            0
        ]

    @property
    def val_root_mean_squared_error(self):
        return self.model_metrics[self.model_metrics["mode"] == "val"]["rmse"].values[0]

    @property
    def test_root_mean_squared_error(self):
        return self.model_metrics[self.model_metrics["mode"] == "test"]["rmse"].values[
            0
        ]

    @property
    def train_r2(self):
        return self.model_metrics[self.model_metrics["mode"] == "train"]["r2"].values[0]

    @property
    def val_r2(self):
        return self.model_metrics[self.model_metrics["mode"] == "val"]["r2"].values[0]

    @property
    def test_r2(self):
        return self.model_metrics[self.model_metrics["mode"] == "test"]["r2"].values[0]

    @property
    def total_buys(self):
        return self.trading_history[self.trading_history["action"] == "buy"].count()[0]

    @property
    def total_sells(self):
        return self.trading_history[self.trading_history["action"] == "sell"].count()[0]

    @property
    def total_do_nothing(self):
        return self.trading_history[
            self.trading_history["action"] == "do_nothing"
        ].count()[0]

    @property
    def asset_periods(self):
        return self.trading_history_descriptive_statistics["count"]

    @property
    def asset_mean(self):
        return self.trading_history_descriptive_statistics["mean"]

    @property
    def asset_min(self):
        return self.trading_history_descriptive_statistics["min"]

    @property
    def asset_inner_quartile(self):
        return self.trading_history_descriptive_statistics["25Q"]

    @property
    def asset_middle_quartile(self):
        return self.trading_history_descriptive_statistics["50Q"]

    @property
    def asset_outer_quartile(self):
        return self.trading_history_descriptive_statistics["75Q"]

    @property
    def asset_max(self):
        return self.trading_history_descriptive_statistics["max"]

    def annualized_std(self, series: pd.Series = None):
        """
        Calculates the annualized standard deviation of an hourly
        pandas Series that has been sorted in ascending time series
        order.
        """

        if series is None:
            series = self.trading_history["total_assets"]

        log_differential = np.log(series / series.shift(-1))
        hourly_std = np.std(log_differential)
        annualized_std = hourly_std * np.sqrt(365)
        return annualized_std

    def generate_line_plot(
        self,
        y_array: np.array,
        x_axis_title: str,
        y_axis_title: str,
        graph_title: str,
        y_axis_unit: str = None,
        x_array: np.array = None,
    ) -> go.Figure:
        """A plotly line plot from the provided array."""

        if x_array is None:
            x_array = np.arange(len(y_array))

        layout = go.Layout(
            title=go.layout.Title(text=str(graph_title).title()),
            xaxis=go.layout.XAxis(title=x_axis_title),
            yaxis=go.layout.YAxis(title=y_axis_title),
        )

        fig = go.Figure(layout=layout)
        fig.add_trace(
            go.Scatter(
                x=x_array, y=y_array, mode="lines", name=str(graph_title).title()
            ),
        )

        if y_axis_unit is not None:
            fig.update_layout(yaxis_tickformat=y_axis_unit)

        return fig

    def _generate_kpi_plot(self, current_value: float, initial_value: float, text: str = '', subtitle: str = '', unit: str = ''):
        """Generates a single KPI Plot"""
        fig = go.Figure()
        kpi_text = f"""{str(text).title()}<br><span style="font-size:0.8em;color:gray">{subtitle}</span>"""
        indicator_params = {
                "mode": "number+delta",
                "value": current_value,
                "title": {"text": kpi_text},
                "delta": {"reference": initial_value, "relative": True},
            }
        if unit == "$":
            indicator_params["number"] = {"prefix": "$"}
        indicator = go.Indicator(**indicator_params)
        return indicator

    def generate_kpi_plot(
        self,
        current_values: List[float],
        initial_values: List[float],
        texts: List[str] = [""],
        subtitles: List[str] = [""],
        units: List[str] = [""],
    ) -> go.Figure:
        """Generates a plotly KPI Plot."""

        number_of_kpis = len(current_values)
        fig = go.Figure()

        assert len(current_values) == len(
            initial_values
        ), f"""
current_values and initial_values are not the same length\ncurrent_values: {len(current_values)} | initial_values: {len(initial_values)}"""

        for idx, _ in enumerate(current_values):
            current_value = current_values[idx]
            initial_value = initial_values[idx]
            try:
                text = texts[idx]
            except IndexError:
                pass
            try:
                subtitle = subtitles[idx]
            except IndexError:
                pass
            try:
                unit = units[idx]
            except IndexError:
                pass

            kpi_text = f"""{str(text).title()}<br><span style="font-size:0.8em;color:gray">{subtitle}</span>"""
            column = idx + 1
            row = 1

            indicator_params = {
                "mode": "number+delta",
                "value": current_value,
                "title": {"text": kpi_text},
                "delta": {"reference": initial_value, "relative": True},
                "domain": {"row": row, "column": column},
            }
            if unit == "$":
                indicator_params["number"] = {"prefix": "$"}
            indicator = go.Indicator(**indicator_params)
            fig.add_trace(indicator)

        fig.update_layout(grid={"rows": 1, "columns": number_of_kpis + 1})

        return fig

    @staticmethod
    def generate_card(html_element: str, card_title: str, p_text: str = ""):
        card = f"""
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">{card_title}</h5>
                <p class="card-text">{p_text}</p>
            </div>
            {html_element}
        </div>
        """
        return card
