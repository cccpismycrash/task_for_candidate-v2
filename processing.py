import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import ta
from openpyxl import load_workbook
from datetime import datetime, timezone

from datetime import timedelta

from tinkoff.invest import CandleInterval, Client, InstrumentIdType, HistoricCandle
from matplotlib.dates import DateFormatter
from matplotlib.lines import Line2D
import matplotlib.image as mpimg
from config_reader import config

# необходимо вставить свой токен!!!
TOKEN = config.API_TOKEN

wb_name = 'stock-index-base-moex-rts-18122012-nowadays.xlsx'

def utcnow():
    return datetime.now(timezone.utc)

def create_df(candles: [HistoricCandle], j):
    df = pd.DataFrame([{
        'time': c.time,
        # 'volume': c.volume,
        # 'open': cast_money(c.open),
        f'{j}': cast_money(c.close),
        # 'high': cast_money(c.high),
        # 'low': cast_money(c.low),
    } for c in candles])

    return df

def create_df_without_date(candles: [HistoricCandle], j):
    df = pd.DataFrame([{
        # 'time': c.time,
        # 'volume': c.volume,
        # 'open': cast_money(c.open),
        f'{j}': cast_money(c.close),
        # 'high': cast_money(c.high),
        # 'low': cast_money(c.low),
    } for c in candles])

    return df

def cast_money(v):
    return v.units + v.nano / 1e9

def sma_normal(df, norm_col, window=50):
    for i in norm_col:
        df[f'{i}_sma'] = ta.trend.sma_indicator(close=df[f'{i}'], window=window, fillna=False)
    return df

def sma_problem(df, prob_col, window=50):
    for i in prob_col:
        df_problem = df[['time', f'{i}']]
        df_problem = df_problem.dropna()
        df_problem[f'{i}_sma'] = ta.trend.sma_indicator(close=df_problem[f'{i}'], window=window, fillna=False)
        df = pd.merge(left=df, right=df_problem[['time', f'{i}_sma']], how='outer', left_on='time', right_on='time')
    return df

def parse_wb(wb_name):
    wb = load_workbook(wb_name)
    sheets = wb.get_sheet_names()

    list_imoex = []
    for sheet in sheets[1:]:
        df = pd.read_excel('stock-index-base-moex-rts-18122012-nowadays.xlsx', sheet_name=sheet, skiprows=3)
        df = df.dropna(subset=['№'])

        start = wb[f'{sheet}']['C2'].value
        if isinstance(start, str): 
            start = start[:10]
            start = datetime.strptime(start, '%d.%m.%Y')
        start = start.replace(tzinfo=timezone.utc)
        
        end = wb[f'{sheet}']['D2'].value
        
        if isinstance(end, str): 
            end = end[:10]
            end = datetime.strptime(end, '%d.%m.%Y')
        
        if end == None: end = utcnow()
        else: end = end.replace(tzinfo=timezone.utc) 

        list_imoex.append((df, {'start': start,'end': end}))

    today = utcnow()
    one_year_ago = utcnow() - timedelta(days=365)

    new_list_imoex = [
        (df, dict_date) for df, dict_date in list_imoex
        if (
            (dict_date['start'] >= one_year_ago and
            dict_date['end'] <= utcnow()) or
            (dict_date['start'] <= one_year_ago and
            dict_date['end'] >= one_year_ago)
            )
    ]

    df_code = pd.DataFrame()
    for i in range(len(new_list_imoex)):
        df_code = pd.concat([df_code, new_list_imoex[i][0]['Code']], axis=0)

    df_code.columns = ['ticker']

    unique_code = df_code['ticker'].unique()
    unique_code_list = list(unique_code)
    return unique_code_list, new_list_imoex

def import_candles(i, j, df_quotes):
    with Client(TOKEN) as client:
        figi = client.instruments.share_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
            id = j,
            class_code='TQBR'
        )

        figi = figi.instrument.figi
        
        r = client.market_data.get_candles(
            figi=figi,
            from_=utcnow() - timedelta(days=450),
            to=utcnow(), 
            interval=CandleInterval.CANDLE_INTERVAL_DAY
        )
        
        df = create_df(r.candles, j)

        if i == 0:
            df = create_df(r.candles, j)
            df_quotes = pd.concat([df_quotes, df], axis=1)
        else:
            df = create_df(r.candles, j)    
            df_quotes = pd.merge(left=df_quotes, right=df, how='outer', left_on='time', right_on='time')
    return df_quotes

def make_pic():

    unique_code_list, new_list_imoex = parse_wb(wb_name)

    df_quotes = pd.DataFrame()

    for i, j in enumerate(unique_code_list):

        df_quotes = import_candles(i, j, df_quotes)


    with Client(TOKEN) as client:
        imoex_info = client.instruments.indicatives(
            request=()
        )

        imoex_info = imoex_info.instruments

        for item in imoex_info:
            if item.ticker == 'IMOEX':
                result = item
                break


        r = client.market_data.get_candles(
            instrument_id=result.uid,
            from_=utcnow() - timedelta(days=450),
            to=utcnow(), 
            interval=CandleInterval.CANDLE_INTERVAL_DAY
        )
        
        candles_imoex = create_df(r.candles, 'IMOEX')

        candles_imoex = candles_imoex[candles_imoex['time'] > (utcnow()-timedelta(days=365))]

        df_work = df_quotes

    empty_columns = df_work.isnull().any()
    columns_with_empty_values = empty_columns[empty_columns].index.tolist()
    problem_columns = [col for col in columns_with_empty_values if col in df_work.columns]
    normal_columns = [col for col in df_work.columns if col not in columns_with_empty_values]
    normal_columns.remove('time')

    df_work = sma_problem(df_work, problem_columns, window=50)

    df_work = sma_normal(df_work, normal_columns, window=50)

    df_result = pd.DataFrame()

    for df, date_dict in new_list_imoex:
        code_list = df['Code'].tolist()
        
        tickers = list()
        for code in code_list:
            tickers.append(code)    
            tickers.append(f'{code}_sma')
        count_code = len(tickers)

        tickers.append('time')
        
        df_cycle = df_work[tickers]

        count_code = len(code_list)
        
        start = date_dict['start']
        end = date_dict['end']

        df_cycle = df_cycle[(df_cycle['time'] >= start) & (df_cycle['time'] <= end)]

        df_temp = pd.DataFrame()

        df_temp = pd.concat([df_temp, df_cycle['time']], axis=1)
    
        for i, j in enumerate(code_list):
            df_cycle[f'{j}_target'] = (df_cycle[f'{j}'] > df_cycle[f'{j}_sma'])*1
            df_temp = pd.merge(left=df_temp, right=df_cycle[['time', f'{j}_target']], how='outer', left_on='time', right_on='time')

        df_temp['sum'] = df_temp[[f'{col}_target' for col in code_list]].sum(axis=1)
        df_temp['percentage'] = np.round((df_temp['sum'] / count_code)*100, 2)
        df_result = pd.concat([df_temp[['time', 'percentage']], df_result], axis=0)

    df_result = df_result[df_result['time'] > (utcnow()-timedelta(days=365))]
    df_result = pd.merge(left=df_result, right=candles_imoex, how='inner', left_on='time', right_on='time')

    fig, ax = plt.subplots(figsize=(9, 5))
    ax1 = ax.twinx()
    ax.plot(df_result['time'], df_result['percentage'], color='black', label='Доля акций')
    ax.spines['left'].set_visible(False)
    ax.set_ylabel('%', rotation=0, loc='bottom', labelpad=10)

    ylabel = ax.yaxis.get_label()
    ylabel.set_verticalalignment('bottom')
    ylabel.set_horizontalalignment('right')
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.legend()

    ax1.plot(df_result['time'], df_result['IMOEX'], color='red', label='IMOEX')
    ax1.xaxis.set_major_formatter(DateFormatter('%b %Y'))
    ax1.set_ylabel('points', rotation=0, loc='bottom', labelpad=20)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_visible(False)

    ylabel = ax1.yaxis.get_label()
    ylabel.set_verticalalignment('bottom')
    ylabel.set_horizontalalignment('right')

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Доля акций', markerfacecolor='black', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='IMOEX', markerfacecolor='red', markersize=10)
    ]

    ax.legend(handles=legend_elements, loc='upper right', frameon=False)

    logo_path = 'small_logo.png'
    logo = mpimg.imread(logo_path)

    ax.figure.figimage(logo,
                    ax.bbox.xmax//2 - logo.shape[0]//2,
                    ax.bbox.ymax//2 - logo.shape[1]//2,
                    alpha=.25, zorder=5)

    bbox_properties = dict(
        boxstyle='circle, pad=0.001',
        ec='lightgray',
        fc='lightgray',
        ls='-',
        lw=3
    )

    plt.text(0.98, 1.15, "headlines", fontsize=9, ha='right', va='top', transform=ax.transAxes, bbox=bbox_properties)

    plt.title('\nДоля акций эмитентов в IMOEX, \nторгующихся выше 50-дневной MA\n', loc='left', )
    plt.tight_layout()
    # plt.show()
    plt.savefig(fname='result.png')

    return datetime.strftime(df_result['time'].iloc[-1], '%d.%m.%Y'), df_result['percentage'].iloc[-1]