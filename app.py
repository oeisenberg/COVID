import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html

from requests import get
from scipy import signal
from plotly.subplots import make_subplots

def get_data(url):
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

def generate_linegraph_cases(x, y): 
    def get_dayDeltaAsStr(numb_cases):
        delta = numb_cases[-1:][0] - numb_cases[-2:-1][0]
        if delta > 0:
            indicator = "+"
        else:
            indicator = ""
        return '(' + indicator + str(delta) + ')'

    fig = make_subplots(specs=[[{"secondary_y": False}]])
    fig.add_trace(
        go.Scatter(x=x, y=y, name="Raw Data"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=x, y=signal.savgol_filter(y, 7, 3), name="7 Day Average"),
        secondary_y=False,
    )

    # fig.add_trace(
    #     go.Scatter(x=x, y=np.diff(y), name="Rate of Change"),
    #     secondary_y=True,
    # )

    fig.update_layout(
        title_text="Number of COVID-19 Cases within England " + get_dayDeltaAsStr(y),
        title_x=0.5
    )
    fig.update_xaxes(title_text="Time", range=[x[60],x[-1]])
    fig.update_yaxes(title_text="Number of Cases", secondary_y=False)
    # fig.update_yaxes(title_text="<b>secondary</b> yaxis title", secondary_y=True)

    return fig

def generate_piecharts_mfCases(data):
    female_data = list(zip(*[[value.get("age"), value.get("rate"), value.get("value")] for value in data.get("data")[0].get("female")]))
    male_data = list(zip(*[[value.get("age"), value.get("rate"), value.get("value")] for value in data.get("data")[0].get("male")]))

    pies = make_subplots(rows=1, cols=3, specs=[[{'type':'domain'}, {'type':'domain'}, {'type':'domain'}]])
    pies.add_trace(go.Pie(labels=female_data[0], values=female_data[2], hole=.3, title="Female"), 1, 1)
    pies.add_trace(go.Pie(labels=male_data[0], values=male_data[2], hole=.3, title="Male"), 1, 2)
    # pies.add_trace(go.Pie(labels=female_data[0], values=[female_data[2][i]-male_data[2][i] for i in range(len(female_data[2]))], hole=.3), 1, 3) # ordered by case number so need to sort
    pies.update_layout(
        title_text="Female and Male case numbers by age category",
        title_x=0.5
    )
    return pies

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

url = (
    'https://api.coronavirus.data.gov.uk/v1/data?'
    'filters=areaType=nation;areaName=england&'
    'structure={"date":"date","newCases":"newCasesByPublishDate"}'
)
data = get_data(url)
x, y = zip(*[[value.get("date"), value.get("newCases")] for value in data.get("data")[::-1]])
fig = generate_linegraph_cases(x, y)

df = pd.DataFrame({"Dates": x, "Number of Cases": y})

url = (
    'https://api.coronavirus.data.gov.uk/v1/data?'
    'filters=areaType=nation;areaName=england&'
    'structure={"male":"maleCases","female":"femaleCases"}'
)
pie_data = get_data(url)
pies = generate_piecharts_mfCases(pie_data)

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

    generate_table(pd.DataFrame.transpose(df[-10::])),

    dcc.Graph(
        id='Pies',
        figure=pies
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)