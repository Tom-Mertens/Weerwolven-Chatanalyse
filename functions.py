import pandas as pd
import datetime

def read_chat(chat):
    timestamps = []
    contacts = []
    messages = []

    for line in chat:
        line = line.strip("\n")
        if line[6:10] == '2021':
            timestamps.append(line[:17])
            if len(line[20:].split(':')) == 1:
                contacts.append('System Generated')
                messages.append(line[20:])
            else:
                contacts.append(line[20:].split(':')[0])
                messages.append("".join(line[20:].split(':')[1:]))  # does remove ':' maar dat maakt niet uit.
        else:
            if len(line) >= 1:
                messages[-1] += line
    df = pd.DataFrame({'Timestamp': timestamps, 'Contact': contacts, 'Message': messages})
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True)
    df = df[df['Contact'] != 'System Generated']
    df = df.reset_index(drop=True)
    return df

def create_dict_list_of_names(df):
    dictlist = []
    unique_list = df['Contact'].unique()
    for name in unique_list:
        dictlist.append({'value': name, 'label': name})
    return dictlist

def create_dict_list_of_dates(df):
    dictlist = []
    df['dates'] = df['Timestamp'].dt.date
    for date in df['dates'].unique():
        dictlist.append({'value': date, 'label': date})
    return dictlist

def divide_days(df):
    # full df, now divide per game day (split at 19:00)
    game_days={}
    for game_date in df['Timestamp'].dt.date.unique()[1:]:
        p1 = df[(df['Timestamp'].dt.date == game_date) & (df['Timestamp'].dt.hour < 19)]
        p2 = df[(df['Timestamp'].dt.date == (game_date - datetime.timedelta(days=1))) & (df['Timestamp'].dt.hour >= 19)]
        game_day = pd.concat([p2, p1])
        # add full day:
        game_days[game_date.strftime("%d-%m-%Y_df")] = game_day.to_json()
        # add contacts only:
        day_contacts = game_day[['Contact', 'Message']].groupby(by='Contact').count()
        game_days[game_date.strftime("%d-%m-%Y_Berichten per persoon")]= day_contacts
    return game_days
