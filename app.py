import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html

from requests import get
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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

url = (
        'https://api.coronavirus.data.gov.uk/v1/data?'
        'filters=areaType=nation;areaName=england&'
        'structure={"date":"date","newCases":"newCasesByPublishDate"}'
)

data = get_data(url)
x, y = zip(*[[value.get("date"), value.get("newCases")] for value in data.get("data")[::-1]])
df = pd.DataFrame({"Dates": x, "Number of Cases": y})
fig = px.line(df, x="Dates", y="Number of Cases")

url = (
        'https://api.coronavirus.data.gov.uk/v1/data?'
        'filters=areaType=nation;areaName=england&'
        'structure={"male":"maleCases","female":"femaleCases"}'
)

data = get_data(url)
female_data = list(zip(*[[value.get("age"), value.get("rate"), value.get("value")] for value in data.get("data")[0].get("female")]))
male_data = list(zip(*[[value.get("age"), value.get("rate"), value.get("value")] for value in data.get("data")[0].get("male")]))
female_df = pd.DataFrame({"Age Categories": female_data[0], "rate": female_data[1], "value": female_data[2]})
male_df = pd.DataFrame({"Age Categories": male_data[0], "rate": male_data[1], "value": male_data[2]})
female_pie = px.pie(female_df, values='value', names='Age Categories', title='Female Cases by Age')
male_pie = px.pie(male_df, values='value', names='Age Categories', title='Male Cases by Age')

pies = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
pies.add_trace(go.Pie(labels=female_data[0], values=female_data[2], hole=.3), 1, 1)
pies.add_trace(go.Pie(labels=male_data[0], values=male_data[2], hole=.3), 1, 2)
pies.update_layout(
    title_text="Female and Male case numbers by age category",
    title_x=0.5
)

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