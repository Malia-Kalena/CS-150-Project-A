import dash
from dash import dcc, html
import dash.dependencies as dd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Preparing your data for usage *******************************************

# Load dataset
df = pd.read_csv(r"C:\Users\mkdej\Topics\PythonProject\PythonProject\Project-A-Malia-Kalena\hawaii_2023_aqs_PM2.5_report.csv")

df.columns = df.columns.str.strip()  # Clean column names

# Remove negative PM2.5 values
df = df[df["Daily Mean PM2.5 Concentration"] >= 0]

df["Date"] = pd.to_datetime(df["Date"])  # Make sure Date is in datetime format
df = df[(df["Date"] >= "2023-01-01") & (df["Date"] <= "2023-12-31")]  # Full-year filter (2023)

# Group by Date & Local Site Name (take mean of PM2.5 values per site and date)
df = df.groupby(["Date", "Local Site Name"], as_index=False)["Daily Mean PM2.5 Concentration"].mean()

# Get unique locations
unique_sites = df["Local Site Name"].unique()

app = dash.Dash(__name__)


# App Layout *******************************************

app.layout = html.Div(
    [
        # Main title
        html.Div(
            html.H1(
                "Hawaii Air Quality Analysis: Lahaina Fire Impact",
                style={"textAlign": "center"}
            ),
            style={"padding": "20px"},
        ),

        # Dropdown
        html.Div(
            dcc.Dropdown(
                        id="site-dropdown",
                        options=[{"label": site, "value": site} for site in unique_sites],
                        value=list(unique_sites),  # Default to all locations selected
                        multi=True,  # Allow multiple selections
                        clearable=False,
            ),
            style={"margin": "20px"},
        ),

        # Date picker
        html.Div(
            dcc.DatePickerRange(
                        id="date-picker",
                        start_date="2023-07-01",  # Default start date: July 1, 2023
                        end_date="2023-08-31",  # Default end date: August 31, 2023
                        min_date_allowed="2023-01-01",  # Earliest selectable date
                        max_date_allowed="2023-12-31",  # Latest selectable date
                        display_format="YYYY-MM-DD",
            ),
            style={"margin": "20px"},
        ),

        html.Div(
            dcc.Graph(id="pm25-line-chart"),
            style={"margin": "20px"},
        ),
    ]
)


# Callbacks *******************************************

@app.callback(
    dd.Output("pm25-line-chart", "figure"),
    [
        dd.Input("site-dropdown", "value"),
        dd.Input("date-picker", "start_date"),
        dd.Input("date-picker", "end_date"),
    ]
)
def update_figure(selected_sites, start_date, end_date):
    # Filter data by date
    filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    # If no site selected, return empty figure
    if not selected_sites:
        return go.Figure(layout={"title": "No locations selected"})

    # Filter by selected locations
    filtered_df = filtered_df[filtered_df["Local Site Name"].isin(selected_sites)]

    # Handle missing dates by resampling
    all_dates = pd.date_range(start=filtered_df["Date"].min(), end=filtered_df["Date"].max(), freq="D")  # list of daily timestamps from earliest to latest date

    # resample to include missing dates
    filtered_df = (
        filtered_df.set_index("Date")  # "Date" as index
        .groupby("Local Site Name", group_keys=False)  # Group data by site, avoid duplicate columns issue
        .apply(lambda x: x.reindex(all_dates))  # Reindex each site's data to match all dates
        .reset_index()
    )
    filtered_df.rename(columns={"index": "Date"}, inplace=True)

    # If no data after filtering, return empty figure
    if filtered_df.empty:
        return go.Figure(layout={"title": "No data available for selected range"})

    # Use 'linear' line_shape to prevent jumps
    fig = px.line(
        filtered_df, x="Date", y="Daily Mean PM2.5 Concentration",
        color="Local Site Name",
        title="PM2.5 Levels Over Time",
        labels={"Daily Mean PM2.5 Concentration": "PM2.5 (µg/m³)", "Local Site Name": "Location"},
        markers=True,
        line_shape="linear"  # Prevents sudden jumps in the graph
    )

    # Add vertical dashed line for August 8, 2023 (Lahaina fire)
    if (filtered_df["Date"] >= "2023-08-08").any():
        max_pm25 = filtered_df["Daily Mean PM2.5 Concentration"].max()

        fig.add_shape(
            type="line",
            x0="2023-08-08", x1="2023-08-08",
            y0=0, y1=max_pm25,
            line=dict(color="black", width=2, dash="dash"),
        )

        fig.add_annotation(
            x="2023-08-08",
            y=1,
            yref="paper",
            text="Lahaina Fire (Aug 8)",
            showarrow=True,
            arrowhead=2,
            ax=50,
            ay=-40,
            bgcolor="white",
            bordercolor="black",
        )

    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
