import pandas as pd 
import yfinance as yf
import datetime as dt
import streamlit as st

###### Initialize Page ######
st.set_page_config(page_title='Historical Stock Earnings Move', page_icon='🚀')

###### Initialize Function ######
def get_earnings_data(stock_ticker_input):

  stock = yf.Ticker(stock_ticker_input)

  today_date = dt.datetime.today()
  start_date = today_date - dt.timedelta(weeks=52*4)

  data = stock.history(start=start_date, end=today_date)
  data = data.reset_index()
  data['Date'] = data['Date'].dt.date
  data.tail()

  earnings_dates = stock.get_earnings_dates(limit=20)
  earnings_dates = earnings_dates.dropna()
  earnings_dates = earnings_dates[::-1].reset_index()
  earnings_dates['Date'] = earnings_dates['Earnings Date'].dt.date

  df = pd.DataFrame()

  for date in earnings_dates['Date']:

    df_working = data.loc[data['Date'] == date].copy()
    idx = data.loc[data['Date'] == date].index

    df_working['Close Before Earnings'] = data['Close'].iloc[idx-1].values
    df_working['Close After Earnings'] = data['Close'].iloc[idx+1].values
    df_working['+1D %Change'] = 100 * (df_working['Close After Earnings'] - df_working['Close Before Earnings']) / df_working['Close Before Earnings']

    try:
      df_working['Close 7D After Earnings'] = data['Close'].iloc[idx+7].values
      df_working['+7D %Change'] = 100 * (df_working['Close 7D After Earnings'] - df_working['Close Before Earnings']) / df_working['Close Before Earnings']
    except:
      df_working['Close 7D After Earnings'] = None


    df = df.append(df_working)

  df = df[['Date','Close Before Earnings', 'Close After Earnings', '+1D %Change', 'Close 7D After Earnings', '+7D %Change']].copy()
  df = df[::-1].set_index('Date')
  return df


###### Input and get Ticker data ######
with st.form(key='ticker_input'):
	stock_ticker_input = st.text_input(label='Input Stock Ticker', value=None)
	submit_button = st.form_submit_button(label='Submit')
  
try:
  data = get_earnings_data(stock_ticker_input)
  company_name = '$'+stock_ticker_input
  st.markdown('#### 🟢 Showing earnings information for ' + company_name)
except:
  st.markdown('#### ❌ Unable to obtain data. Choose another ticker')

###### Compute & Display Average Metrics ######

avg_1d_move = round(data['+1D %Change'].mean(), 2)
std_1d_move = round(data['+1D %Change'].std(), 2)
avg_7d_move = round(data['+7D %Change'].mean(), 2)
std_7d_move = round(data['+7D %Change'].std(), 2)

avg_delta_7d = round(avg_7d_move - avg_1d_move,2)
std_delta_7d = round(std_7d_move - std_1d_move,2)


col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(label='Average 1D Move', value=str(avg_1d_move)+'%', delta=None, delta_color="normal", help=None, label_visibility="visible")
col2.metric(label='Average 7D Move', value=str(avg_7d_move)+'%', delta=avg_delta_7d, delta_color="normal", help=None, label_visibility="visible")
col4.metric(label='StDev 1D Move', value=str(std_1d_move)+'%', delta=None, delta_color="normal", help=None, label_visibility="visible")
col5.metric(label='StDev 7D Move', value=str(std_7d_move)+'%', delta=std_delta_7d, delta_color="normal", help=None, label_visibility="visible")

###### Display Candlestick ######

###### Display Data Table ######
st.dataframe(data)
