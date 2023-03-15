from dash import Dash, html, dcc, Input, Output, State
from plotly.subplots import make_subplots
import plotly.express as px, plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
import config
import nyseholidays as nh
import datetime
import boto3

connection = sqlite3.connect(config.DB_FILE)

# SQL query to pull stock data from S3
df = pd.read_csv('https://datasetjackapp.s3.us-west-2.amazonaws.com/data.csv')

# Pull calculated holidays from NYSE and current time
cal = nh.USTradingHolidaysCalendar()
holidays = cal.holidays(start='2022-01-01', end='2025-12-31')
now = datetime.datetime.now()

# Pull current list of S&P 500 from Wikipedia
# table=pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
# df_snp = table[0]
# snp_list = sorted(df_snp['Symbol'].values.tolist())

snp_list = ['AAPL', 'TSLA']

# Start Dash app
app = Dash(__name__)

config = dict({
    'scrollZoom': True, 
    'modeBarButtonsToRemove':['autoScale', 'zoom', 'zoomIn', 'zoomOut'],
    'displaylogo': False
    })

app.layout = html.Div(children=[
    html.H1(children='Jack app',
            style={'textAlign':'center',
                   'color':'#ffffff'}),

    html.Div(children=f'Example historical stock price for S&P stocks.',
        style={'textAlign':'center',
                'color':'#ffffff'}),

    dcc.Dropdown(id='stock_dropdown',
                options = [{'label': s, 'value': s} for s in snp_list],
                value='AAPL'),

    html.Div([
                html.Label(['Choose a graph:'],style={'font-weight': 'bold'}),
                dcc.RadioItems(
                    id='graph_type',
                    options=[
                             {'label': 'Line', 'value': 'line'},
                             {'label': 'Candlestick', 'value': 'candle'}
                    ],
                    value='line',
                    style={"width": "60%"}
                ),
        ]),

    dcc.Graph(id='graph',
              config=config)
    
])

@app.callback(
    Output('graph', 'figure'),
    [Input('stock_dropdown', 'value'), Input('graph_type', 'value')]
)

def graph_update(dropdown_value, graph_type):
    
    print(dropdown_value)
    print(graph_type)
    print("Current time =", now.strftime("%Y-%m-%d %H:%M:%S"))


    # df2 = df.filter(like=dropdown_value, axis=0).sort_values(by='date')
    df2 = df.loc[df['symbol'] == dropdown_value].sort_values(by='date')

    if graph_type == 'line':
        fig = px.line(df2, x="date", y="close", template='plotly_dark')

        fig['data'][0]['line']['color']='aqua'

        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat","mon"]),  #hide weekends
                dict(values=holidays)  # hide holidays
            ],
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="<b>1m</b>", step="month", stepmode="backward"),
                    dict(count=6, label="<b>6m</b>", step="month", stepmode="backward"),
                    dict(count=1, label="<b>YTD</b>", step="year", stepmode="todate"),
                    dict(count=1, label="<b>1y</b>", step="year", stepmode="backward"),
                    dict(label="<b>ALL</b>", step="all")
                ])
            )
        )

        fig.update_layout(xaxis_rangeselector_font_color='black',
                    xaxis_rangeselector_activecolor='red',
                    xaxis_rangeselector_bgcolor='aqua',
                    dragmode='pan'
                    )
        return fig
    
    else:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(go.Candlestick(x=df2['date'],
                                    open=df2['open'],
                                    high=df2['high'],
                                    low=df2['low'],
                                    close=df2['close']),
                                    secondary_y=False)
        
        fig.add_trace(go.Bar(x=df2['date'],
                               y=df2['volume'],
                               opacity=0.3,
                               marker=dict(color='white')),
                               secondary_y=True)
        
        fig.layout.yaxis2.showgrid=False

        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat","mon"]),  #hide weekends
                dict(values=holidays)  # hide holidays
            ],
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="<b>1m</b>", step="month", stepmode="backward"),
                    dict(count=6, label="<b>6m</b>", step="month", stepmode="backward"),
                    dict(count=1, label="<b>YTD</b>", step="year", stepmode="todate"),
                    dict(count=1, label="<b>1y</b>", step="year", stepmode="backward"),
                    dict(label="<b>ALL</b>", step="all")
                ])
            )
        )
        
        fig.update_layout(template='plotly_dark',
                    xaxis_rangeselector_font_color='black',
                    xaxis_rangeselector_activecolor='red',
                    xaxis_rangeselector_bgcolor='aqua',
                    yaxis2=dict(showticklabels=False,
                                range=[0, df2['volume'].max()*3]),
                    showlegend=False,
                    dragmode='pan'
                    )
        
        
        return fig

if __name__ == '__main__':
    app.run_server(debug=True)

