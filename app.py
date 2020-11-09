import dash
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from requests import get
from scipy import signal
from datetime import datetime, timedelta
from plotly.subplots import make_subplots


def get_data(url, timeout=10):
    def check_data(url, timeout):
        response = get(url, timeout)

        if response.status_code >= 400:
            raise RuntimeError(f'Request failed: {response.text}')

        if response.status_code == 204:
            raise RuntimeError(f'Request failed: {response.text}')

        return response.json()

    try:
        return check_data(url, timeout)
    except:
        return {}


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


def generate_linegraph_cases(x, y, y2):
    def get_dayDeltaAsStr(numb_cases):
        delta = numb_cases[-1:][0] - numb_cases[-2:-1][0]
        if delta > 0:
            indicator = "+"
        else:
            indicator = ""
        return '(' + indicator + str(delta) + ')'

    if len(data) == 0:
        return {}

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=x, y=y, name="Raw Data"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=x, y=signal.savgol_filter(
            y, 7, 3), name="7 Day Case Average"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=x, y=y2, name="Deaths"),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(x=x, y=signal.savgol_filter(
            y2, 7, 3), name="7 Day Death Average"),
        secondary_y=True,
    )

    fig.update_layout(
        title_text="Number of COVID-19 Cases within England " +
        get_dayDeltaAsStr(y),
        title_x=0.5
    )
    fig.update_xaxes(title_text="Time", range=[x[60], x[-1]])
    fig.update_yaxes(title_text="Number of Cases", secondary_y=False)
    fig.update_yaxes(title_text="Number of Deaths", secondary_y=True)

    return fig


def generate_piecharts_mfCases(data):
    if len(data) == 0:
        return {}

    female_data = list(zip(*[[value.get("age"), value.get("rate"), value.get("value")]
                             for value in data.get("data")[0].get("female")]))
    male_data = list(zip(*[[value.get("age"), value.get("rate"), value.get("value")]
                           for value in data.get("data")[0].get("male")]))

    pies = make_subplots(rows=1, cols=3, specs=[
                         [{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]])
    pies.add_trace(go.Pie(
        labels=female_data[0], values=female_data[2], hole=.3, title="Female"), 1, 1)
    pies.add_trace(
        go.Pie(labels=male_data[0], values=male_data[2], hole=.3, title="Male"), 1, 2)
    # pies.add_trace(go.Pie(labels=female_data[0], values=[female_data[2][i]-male_data[2][i] for i in range(len(female_data[2]))], hole=.3), 1, 3) # ordered by case number so need to sort
    pies.update_layout(
        title_text="Female and Male case numbers by age category",
        title_x=0.5
    )
    return pies


def create_card(card_id, title, description):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4(title, id=f"{card_id}-title"),
                html.H2("100", id=f"{card_id}-value"),
                html.P(description, id=f"{card_id}-description")
            ]
        )
    )


def create_map(data):
    if len(data) == 0:
        return {}

    dates, area, cases = zip(*[[value.get("date"), value.get("areaName"),
                                value.get("newCases")] for value in data.get("data")[::-1]])
    df = pd.DataFrame({"Date": dates, "Area": area, "Number of Cases": cases})

    f = open("geo.json", "r")
    geojson = json.load(f)

    fig = px.choropleth_mapbox(df, geojson=geojson, color="Number of Cases",
                               locations="Area", featureidkey="properties.lad15nm",
                               center={"lat": 51.509865, "lon": -0.128092},
                               mapbox_style="carto-positron", zoom=7, height=800)

    return fig


def create_map_animation():
    def get_nDays(n=7, format="%d-%m-%Y"):
        today = datetime.today()
        dates = []
        for day in range(n, 0, -1):
            date = today - timedelta(days=day-1)
            dates.append(date.strftime(format))
        return dates

    f = open("geo.json", "r")
    geojson = json.load(f)

    dates = get_nDays(31, format="%Y-%m-%d")
    url = (
        'https://api.coronavirus.data.gov.uk/v1/data?'
        'filters=areaType=ltla;date=' + dates[0] + '&'
        'structure={"date":"date","newCases":"newCasesByPublishDate","areaName":"areaName"}'
    )
    data = get_data(url, 50)
    data_dates, area, cases = zip(*[[value.get("date"), value.get(
        "areaName"), value.get("newCases")] for value in data.get("data")[::-1]])
    df = pd.DataFrame(
        {"Date": data_dates, "Area": area, "Number of Cases": cases})
    fig = go.Figure(data=go.Choroplethmapbox(
        locations=df["Area"],
        z=df["Number of Cases"],
        geojson=geojson,
        featureidkey="properties.lad15nm",
        zmin=0,
        zmax=500
    ))

    frames = []
    for date in dates[1::]:
        url = (
            'https://api.coronavirus.data.gov.uk/v1/data?'
            'filters=areaType=ltla;date=' + date + '&'
            'structure={"date":"date","newCases":"newCasesByPublishDate","areaName":"areaName"}'
        )
        data = get_data(url)
        data_dates, area, cases = zip(*[[value.get("date"), value.get(
            "areaName"), value.get("newCases")] for value in data.get("data")[::-1]])
        df = pd.DataFrame(
            {"Date": data_dates, "Area": area, "Number of Cases": cases})
        frames.append(go.Frame(data=[
            go.Choroplethmapbox(
                locations=df["Area"],
                z=df["Number of Cases"],
                geojson=geojson,
                featureidkey="properties.lad15nm",
                zmin=0,
                zmax=500
            )
        ],
        traces=[0, 1, 2],
        name=f'fr{date}'))

    # transitions may not be supported
    frame_duration, transition_duration = 500, 500
    button_anim = dict(
        label='Play Animation',
        method='animate',
        args=[None, dict(frame=dict(duration=frame_duration, redraw=True),
                         transition=dict(
                             duration=transition_duration, easing="quadratic-in-out"),
                         fromcurrent=False)])

    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=5,
                      height=800,
                      mapbox_center={"lat": 53.54865, "lon": -0.158092},
                      updatemenus=[{'type': 'buttons',
                                    'buttons': [button_anim],
                                    'x': 1,
                                    'y': -0.25,
                                    'xanchor': 'left',
                                    'yanchor': 'bottom'}]
                      )
    sliders = [dict(steps=[dict(method='animate',
                                args=[[f'fr{date}'],
                                      dict(mode='immediate',
                                           frame=dict(
                                               duration=frame_duration, redraw=True),
                                           transition=dict(duration=transition_duration, easing="cubic-in-out"))
                                      ],
                                label=f'Date: {date}'
                                ) for date in dates],
                    x=0,  # slider starting position
                    y=0,
                    len=1.0)  # slider length
               ]

    fig.update_layout(sliders=sliders)
    fig.frames = frames
    return fig


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

url = (
    'https://api.coronavirus.data.gov.uk/v1/data?'
    'filters=areaType=nation;areaName=england&'
    'structure={"date":"date","newCases":"newCasesByPublishDate","newDeaths":"newDeaths28DaysByPublishDate"}'
)
data = get_data(url)
x, y, y2 = zip(*[[value.get("date"), value.get("newCases"),
                  value.get("newDeaths")] for value in data.get("data")[::-1]])
fig = generate_linegraph_cases(x, y, y2)

df = pd.DataFrame({"Dates": x, "Number of Cases": y})

url = (
    'https://api.coronavirus.data.gov.uk/v1/data?'
    'filters=areaType=nation;areaName=england&'
    'structure={"male":"maleCases","female":"femaleCases"}'
)
pie_data = get_data(url)
pies = generate_piecharts_mfCases(pie_data)

# date = "2020-11-07"
# url = (
#     'https://api.coronavirus.data.gov.uk/v1/data?'
#     'filters=areaType=ltla;date=' + date + '&'
#     'structure={"date":"date","newCases":"newCasesByPublishDate","areaName":"areaName"}'
# )
# data = get_data(url, 50)
# ltla_covidmap = create_map(data)
ltla_covidmap = create_map_animation()

app.layout = html.Div(children=[

    # dbc.Row([
    #    dbc.Col([create_card('0', 'Title', 'Description')]), dbc.Col([create_card('1', 'Title', 'Description')])
    # ]),

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
    ),

    dcc.Graph(
        id='ltla_cases',
        figure=ltla_covidmap
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
