import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output
import plotly.express as px
import functions
import pandas as pd
import os
import dash_table

# general settings:
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# data management:
global df
chat = open('./chat_exports/06 - 2004.txt', mode="r", encoding='utf-8').readlines()
df = functions.read_chat(chat)

# filter for dead/alive
global dead

dead = {'2021-04-16 00:00:00': ['Babet'],
        '2021-04-18 12:00:00': ['Sven', 'Bob'],
        '2021-04-19 12:00:00': ['Tom Mertens', 'Jelle Lauf', 'Anke'],
        "2021-04-20 12:00:00": ['Remco', 'Sam']
        }

# for dropdown menus:
dict_names = functions.create_dict_list_of_names(df)
dict_dates = functions.create_dict_list_of_dates(df)


# create html table with votes:
def generate_voting_table():
    vote_df = pd.DataFrame(columns=['Naam'])
    for file in os.listdir(".//stemgedrag//"):
        if 'stemronde' in file:
            tmp_df = pd.read_excel(".//stemgedrag//" + file)
            vote_df = vote_df.merge(tmp_df, how='outer', on='Naam')
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in vote_df.columns])] +
        # Body
        [html.Tr([
            html.Td(vote_df.iloc[i][col]) for col in vote_df.columns
        ]) for i in range(len(vote_df))]
    )


app.layout = html.Div([
    html.Div([
        html.H1('Gemeente Archief Wakkerdam')], style={'width': '100%', 'display': 'inline-block'}),
    html.Div([
        html.H3('1. Berichten per persoon'),
        html.Div([
            html.H5('Data vanaf datum:'),
            dcc.Dropdown(
                id='min_date',
                options=dict_dates,
                multi=False,
                value=df['dates'].to_list()[0],
                clearable=False
            )], style={'width': '20%', 'display': 'inline-block'}),
        html.Div([
            html.H5('Data tot datum:'),
            dcc.Dropdown(
                id='max_date',
                options=dict_dates,
                multi=False,
                value=df['dates'].to_list()[-1],
                clearable=False
            )], style={'width': '20%', 'display': 'inline-block'}),
        html.Div([
            dcc.Graph(
                id='contacts_message_count_graph'
            )], style={'width': '100%', 'display': 'inline-block'})],
        style={'width': '40%', 'display': 'inline-block'}),

    html.Div([
        html.H3(children='2. Stemgedrag Tabel'),
        generate_voting_table()
    ], style={'width': '100%', 'display': 'inline-block'}),

    html.Div([
        html.H3(children="3. Berichten check"),
        html.Div([
            html.H5('Berichten van:'),
            dcc.Dropdown(
                id='who',
                options=dict_names,
                multi=False,
                value='Tom Mertens',
                clearable=False
            )], style={'width': '20%', 'display': 'inline-block'}),
        html.Div([
            html.H5('Berichten vanaf datum:'),
            dcc.Dropdown(
                id='start',
                options=dict_dates,
                multi=False,
                value=df['dates'].to_list()[0],
                clearable=False
            )], style={'width': '10%', 'display': 'inline-block'}),
        html.Div([
            html.H5('Berichten tot datum:'),
            dcc.Dropdown(
                id='end',
                options=dict_dates,
                multi=False,
                value=df['dates'].to_list()[-1],
                clearable=False
            )], style={'width': '10%', 'display': 'inline-block'}),
        html.Div(dash_table.DataTable(
            id='messages_table',
            columns=[{"name": i, "id": i} for i in ['Timestamp', 'Message']],
            style_cell={'textAlign': 'left',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                        'lineHeight': '15px',
                        'minWidth': '150px'}),
            style={'width': '100%', 'display': 'inline-block'})
    ], style={'width': '60%', 'display': 'inline-block'})
])


@app.callback(Output('contacts_message_count_graph', 'figure'),
              [Input('min_date', 'value'), Input('max_date', 'value')])
def create_contacts_graph(min_date="2021-04-06", max_date="2021-04-19"):
    # filter dead people:
    df['Dood'] = 0
    for date in dead.keys():
        df['Dood'] = df.apply(
            lambda x: 1 if (x['Contact'] in dead[date]) & (x['Timestamp'] >= pd.Timestamp(date)) else x['Dood'], axis=1)

    df_filtered = df[(df['Timestamp'] >= min_date) & (df['Timestamp'] < (pd.Timestamp(max_date) + pd.Timedelta("1D")))]
    df_contacts = df_filtered[["Contact", "Message"]].groupby(by='Contact').count().sort_values(by='Message',
                                                                                                ascending=False)
    df_contacts = df_contacts.merge(df_filtered[['Contact', 'Dood']].groupby(by='Contact').last(), left_index=True,
                                    right_index=True)
    figure = px.bar(df_contacts, x=df_contacts.index, y="Message", color='Dood', title='Grafiek Berichten per persoon')
    return figure


@app.callback(Output('messages_table', 'data'),
              [Input('start', 'value'), Input('end', 'value'), Input('who', 'value')])
def generate_messages(start, end, who):
    person_df = \
        df[(df['Contact'] == who) & ((df['Timestamp'] > pd.Timestamp(start)) & (df['Timestamp'] <= (pd.Timestamp(end)
                                                                                                    + pd.Timedelta(
                    '1D'))))][['Timestamp', 'Message']]
    return person_df.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True)
