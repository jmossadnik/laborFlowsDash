import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
#import pathlib

#path = pathlib.Path(__file__).parent.resolve()

# Load your data from "dta.csv"
#df = pd.read_csv(r'{}/dta.csv'.format(path))
df = pd.read_csv('dta.csv')
df = df[df.year >= 1988] # missing months in 1985; hard to impute because it is the beginning
                         # of the timeseries, hence I cut the data for displaying

# create date variable
df['date'] = pd.to_datetime(df['year'].astype(int).astype(str) + '-' + df['month'].astype(int).astype(str) + '-12')
df = df.sort_values(by=['date'], ascending=True)

# Recession periods
recession_periods = [("1990-07-01", "1991-03-01"), ("2001-03-01", "2001-11-01"),
                     ("2007-12-01", "2009-06-01"), ("2020-02-01", "2020-04-01")]

app = dash.Dash(__name__)

# Declare server for Render deployment. Needed for Procfile.
server = app.server

app.title = 'Labor Market Transitions'


# Define the app layout
app.layout = html.Div([
    html.H1("Labor Market Timeseries Dashboard"),
    dcc.Dropdown(
        id='sex-dropdown',
        options=[{'label': sex, 'value': sex} for sex in ['f', 'm', 't']],
        multi=True,
        value=['f', 'm', 't']  # Default selection
    ),
    dcc.Dropdown(
        id='age-dropdown',
        options=[{'label': age, 'value': age} for age in ['16-64', '16-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-64']],
        multi=True,
        value=['16-64']  # Default selection
    ),
    dcc.Dropdown(
        id='timeseries-dropdown',
        options=[
            {'label': 'full-time --> full-time', 'value': 'EfEf'},
            {'label': 'full-time --> part-time', 'value': 'EfEp'},
            {'label': 'full-time --> unemployed', 'value': 'EfU'},
            {'label': 'full-time --> out of labor force', 'value': 'EfN'},
            {'label': 'part-time --> full-time', 'value': 'EpEf'},
            {'label': 'part-time --> part-time', 'value': 'EpEp'},
            {'label': 'part-time --> unemployed', 'value': 'EpU'},
            {'label': 'part-time --> out of labor force', 'value': 'EpN'},
            {'label': 'unemployed --> full-time', 'value': 'UEf'},
            {'label': 'unemployed --> part-time', 'value': 'UEp'},
            {'label': 'unemployed --> unemployed', 'value': 'UU'},
            {'label': 'unemployed --> out of labor force', 'value': 'UN'},
            {'label': 'out of labor force --> full-time', 'value': 'NEf'},
            {'label': 'out of labor force --> part-time', 'value': 'NEp'},
            {'label': 'out of labor force --> unemployed', 'value': 'NU'},
            {'label': 'out of labor force --> out of labor force', 'value': 'NN'},
        ],
        multi=True,
        value=['EfEp']  # Default selection
    ),
    dcc.Dropdown(
        id='seasonal-dropdown',
        options=[
            {'label': 'seasonally adjusted', 'value': 1},
            {'label': 'not seasonally adjusted', 'value': 0}
        ],
        multi=False,
        value=[0]  # Default selection
    ),
    dcc.Dropdown(
        id='flowrate-dropdown',
        options=[
            {'label': 'gross trasition rate', 'value': 1},
            {'label': 'instantaneous transition rate', 'value': 2},
            {'label': 'both (gross = dashed)', 'value': 3}
        ],
        multi=False,
        value=[1]  # Default selection
    ),
    dcc.Graph(id='timeseries-plot'),
])

# Define callback to update the plot
@app.callback(
    Output('timeseries-plot', 'figure'),
    Input('sex-dropdown', 'value'),
    Input('age-dropdown', 'value'),
    Input('timeseries-dropdown', 'value'),
    Input('seasonal-dropdown', 'value'),
    Input('flowrate-dropdown', 'value')
)

def update_plot(selected_sexes, selected_ages, selected_timeseries, seasonal, flowrate):
    filtered_data = df[(df['sex'].isin(selected_sexes)) & (df['age_group'].isin(selected_ages))].copy()

    selected_timeseries_gross = ['rate_{}'.format(i) for i in selected_timeseries]

    if flowrate == 1:
        selected_timeseries = selected_timeseries_gross
    elif flowrate == 3:
        selected_timeseries = list(selected_timeseries_gross + selected_timeseries)

    if seasonal == 1:
        selected_timeseries = [f'{c}_sa' for c in selected_timeseries]
    
    filtered_data['sex_age'] = filtered_data['sex'] + '_' + filtered_data['age_group']
    
    if flowrate == 3:
        filtered_data1 = filtered_data[['age_group', 'sex', 'date', 'sex_age'] + [c for c in selected_timeseries if 'rate_' in c]]
        filtered_data1['type'] = 'gross'
        filtered_data2 = filtered_data[['age_group', 'sex', 'date', 'sex_age'] + [c for c in selected_timeseries if 'rate_' not in c]]
        filtered_data2['type'] = 'instant'

        filtered_data1.columns = filtered_data2.keys()

        filtered_data = pd.concat([filtered_data1, filtered_data2])
        selected_timeseries = [c for c in selected_timeseries if 'rate_' not in c]
        fig1 = px.line(
            filtered_data[filtered_data.type=='gross'],
            x='date',
            y=selected_timeseries,
            color='sex_age',
            line_dash='variable',
            line_dash_map={'gross': 'dashed'},
            title='Labor Market Transitions',
            labels={"sex": "sex", "age group": "age_group"}
        )
        fig2 = px.line(
            filtered_data[filtered_data.type=='instant'],
            x='date',
            y=selected_timeseries,
            color='sex_age',
            title='Labor Market Transitions'
        )
        fig3 = go.Figure(data=fig1.data + fig2.data)
       
        # Add shaded rectangles for NBER recession dates
        for start_date, end_date in recession_periods:
            fig3.add_vrect(x0=start_date, x1=end_date, fillcolor='grey', opacity=0.3)
    else:
        fig = px.line(
            filtered_data,
            x='date',
            y=selected_timeseries,
            color='sex_age',
            title='Labor Market Transitions',
            labels={"sex": "sex", "age group": "age_group"}
        )

        # Add shaded rectangles for NBER recession dates
        for start_date, end_date in recession_periods:
            fig.add_vrect(x0=start_date, x1=end_date, fillcolor='grey', opacity=0.3)
        

    if flowrate == 3:
        return fig3
    else:
        return fig

if __name__ == '__main__':
    app.run_server(debug=True)
