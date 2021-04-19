import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output
import plotly.express as px
import functions
import pandas as pd
import os

# general settings:
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# data management:
global df
chat = open('./chat_exports/05 - 1904.txt', mode="r", encoding='utf-8').readlines()
df = functions.read_chat(chat)

# filter for dead/alive
global dead

dead = {'2021-04-16 00:00:00': ['Babet'],
        '2021-04-18 12:00:00': ['Sven'],
        '2021-04-19 12:00:00': ['Tom Mertens', 'Jelle Lauf', 'Anke'],
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
        html.H1('Gemeente Archief Wakkerdam'),
        html.H3('Berichten per persoon'),
        html.H5('Data vanaf datum:'),
        dcc.Dropdown(
            id='min_date',
            options=dict_dates,
            multi=False,
            value=df['dates'].to_list()
        ),
        html.H5('Data tot datum:'),
        dcc.Dropdown(
            id='max_date',
            options=dict_dates,
            multi=False,
            value=df['dates'].to_list()
        ),
        dcc.Graph(
            id='contacts_message_count_graph'
        ),
        html.H4(children='Stemgedrag Tabel'),
        generate_voting_table()
    ], style={'width': '40%', 'display': 'inline-block'})
])


@app.callback(Output('contacts_message_count_graph', 'figure'),
              [Input('min_date', 'value'), Input('max_date', 'value')])
def create_contacts_graph(min_date, max_date):
    # filter dead people:
    df['Dood'] = 0
    for date in dead.keys():
        df['Dood'] = df.apply(
            lambda x: 1 if (x['Contact'] in dead[date]) & (x['Timestamp'] >= pd.Timestamp(date)) else x['Dood'], axis=1)

    df_filtered = df[(df['Timestamp'] >= min_date) & (df['Timestamp'] <(pd.Timestamp(max_date)+pd.Timedelta("1D")))]
    df_contacts = df_filtered[["Contact", "Message"]].groupby(by='Contact').count().sort_values(by='Message',
                                                                                                ascending=False)
    df_contacts = df_contacts.merge(df_filtered[['Contact','Dood']].groupby(by='Contact').last(),left_index=True, right_index=True)
    figure = px.bar(df_contacts, x=df_contacts.index, y="Message", color='Dood', title='Berichten per persoon')
    return figure


if __name__ == '__main__':
    app.run_server(debug=True)
