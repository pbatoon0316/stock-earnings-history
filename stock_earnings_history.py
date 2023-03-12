import pandas as pd 
import yfinance as yf
import datetime as dt
import streamlit as st
import mplfinance as mpf


###### Initialize Page ######
st.set_page_config(page_title='Historical Stock Earnings Move', page_icon='🚀')
st.set_option('deprecation.showPyplotGlobalUse', False)

###### Initialize Function ######

def get_earnings_data(stock_ticker_input):

  stock = yf.Ticker(stock_ticker_input)
  today_date = dt.datetime.today()
  start_date = today_date - dt.timedelta(weeks=52*4)


  data = stock.history(start=start_date, end=today_date)
  data = data.reset_index()
  data['Date'] = data['Date'].dt.date


  earnings_dates = stock.get_earnings_dates(limit=20)
  earnings_dates = earnings_dates.dropna()
  earnings_dates = earnings_dates[::-1].reset_index()
  earnings_dates['Date'] = earnings_dates['Earnings Date'].dt.date


  earnings = pd.DataFrame()
  for date in earnings_dates['Date']:

    df = data.loc[data['Date'] == date].copy()
    idx = data.loc[data['Date'] == date].index

    df['Close Before Earnings'] = data['Close'].iloc[idx-1].values
    df['Close After Earnings'] = data['Close'].iloc[idx+1].values
    df['+1D %Change'] = 100 * (df['Close After Earnings'] - df['Close Before Earnings']) / df['Close Before Earnings']

    try:
      df['Close 7D After Earnings'] = data['Close'].iloc[idx+7].values
      df['+7D %Change'] = 100 * (df['Close 7D After Earnings'] - df['Close Before Earnings']) / df['Close Before Earnings']
    except:
      df['Close 7D After Earnings'] = None


    earnings = earnings.append(df)

  earnings = earnings[['Date','Close Before Earnings', 'Close After Earnings', '+1D %Change', 'Close 7D After Earnings', '+7D %Change']].copy()
  earnings = earnings[::-1].set_index('Date')
  return data, earnings 


###### Input and get Ticker data ######
with st.form(key='ticker_input'):
	stock_ticker_input = st.text_input(label='Input Stock Ticker', value=None)
	submit_button = st.form_submit_button(label='Submit')
  
try:
  raw_data = get_earnings_data(stock_ticker_input)

  stock_data = raw_data[0].set_index('Date')
  stock_data.index = pd.to_datetime(stock_data.index)

  earnings_data = raw_data[1]

  company_name = '$'+stock_ticker_input.upper()
  st.markdown('##### 🟢 Showing earnings information for ' + company_name)
  
except:
  st.markdown('#### ❌ Unable to obtain data. Choose another ticker')

###### Compute & Display Average Metrics ######

try:
  avg_1d_move = round(earnings_data['+1D %Change'].mean(), 2)
  std_1d_move = round(earnings_data['+1D %Change'].std(), 2)
  avg_7d_move = round(earnings_data['+7D %Change'].mean(), 2)
  std_7d_move = round(earnings_data['+7D %Change'].std(), 2)

  avg_delta_7d = round(avg_7d_move - avg_1d_move,2)
  std_delta_7d = round(std_7d_move - std_1d_move,2)

  low = stock_data['Close'].iloc[-1] * (1 - earnings_data['+1D %Change'].std()/100)
  high = stock_data['Close'].iloc[-1] * (1 + earnings_data['+1D %Change'].std()/100)

  col1, col2, col3, col4 = st.columns(4)
  col1.metric(label='Price', value='$'+str(round(stock_data['Close'].iloc[-1],2)), delta=None, delta_color="normal", help=None, label_visibility="visible")
  col3.metric(label='StDev 1D Move', value=str(std_1d_move)+'%', delta=None, delta_color="normal", help=None, label_visibility="visible")
  col4.metric(label='StDev 7D Move', value=str(std_7d_move)+'%', delta=std_delta_7d, delta_color="normal", help=None, label_visibility="visible")
  st.markdown('##### Expected range is \$' + str(round(low,2)) + ' - \$' + str(round(high,2)))

except:
  None

###### Display Candlestick ######
fig = mpf.plot(stock_data[-100:], type='candle', style='yahoo', 
         hlines=dict(hlines=[low,high],colors=['r','g'],linestyle='--'),
         figratio=(16,7), figscale=0.6)

st.pyplot(fig)


###### Display Data Table ######
try:
  with st.expander('Historical Earnings Data'):
     st.dataframe(data=earnings_data)
except:
  None
