import dash
import pandas as pd
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html

from requests import get

def get_data():
    url = (
        'https://api.coronavirus.data.gov.uk/v1/data?'
        'filters=areaType=nation;areaName=england&'
        'structure={"date":"date","newCases":"newCasesByPublishDate"}'
    )

    response = get(url, timeout=10)

    if response.status_code >= 400:
        raise RuntimeError(f'Request failed: {response.text}')

    return response.json()

def generate_table(dataframe, max_rows=10, max_cols=10):
    return html.Table([
        html.Thead(
            html.Tr([
                html.Th(dataframe.iloc[0][dataframe.columns[iCol]]) for iCol in range(min(dataframe.columns.stop, max_cols))
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][dataframe.columns[iCol]]) for iCol in range(min(dataframe.columns.stop, max_cols))
            ]) for i in range(1, min(len(dataframe), max_rows))
        ])
    ], style={'marginLeft': 'auto', 'marginRight': 'auto'})

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

data = get_data()
x, y = zip(*[[value.get("date"), value.get("newCases")] for value in data.get("data")[::-1]])

df = pd.DataFrame({
    "Dates": x,
    "Number of Cases": y,
})

fig = px.line(df, x="Dates", y="Number of Cases")

app.layout = html.Div(children=[
    html.H1(
        children='COVID-19 Dashboard',
        style={
            'textAlign': 'center'
        }
    ),

    html.Div(children='Data obtained using the GOV UK API', 
        style={
            'textAlign': 'center'
        }
    ),

    dcc.Graph(
        id='COVID',
        figure=fig
    ),

    generate_table(pd.DataFrame.transpose(df[-10::]))
])

if __name__ == '__main__':
    app.run_server(debug=True)