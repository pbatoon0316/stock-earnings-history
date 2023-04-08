import pandas as pd 
import yfinance as yf
import datetime as dt
import streamlit as st
import plotly.graph_objects as go

###### Initialize Page ######
st.set_page_config(page_title='Historical Stock Earnings Move', page_icon='🚀', layout='wide')
st.set_option('deprecation.showPyplotGlobalUse', False)
hide_streamlit_style = """
            <style>
              footer {visibility: hidden;}
              div.block-container{padding-top:2rem;padding-bottom:2rem;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

###### Initialize Function ######
@st.cache_data(ttl=dt.timedelta(hours=12))
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

    earnings = pd.concat([earnings,df])

  earnings = earnings[['Date','Close Before Earnings', 'Close After Earnings', '+1D %Change', 'Close 7D After Earnings', '+7D %Change']].copy()
  earnings = earnings[::-1].set_index('Date')
  return data, earnings 

@st.cache_data(ttl=dt.timedelta(hours=12))
def get_options_expiries(stock_ticker_input):
  stock = yf.Ticker(stock_ticker_input)
  options_expiries = stock.options
  return options_expiries

@st.cache_data(ttl=dt.timedelta(hours=12))
def get_options_open_interest(stock_ticker_input, selected_options_expiry):
  #expiry_date = expiry_dates[selected_options_expiry]
  stock = yf.Ticker(stock_ticker_input)
  options_chain = stock.option_chain(selected_options_expiry)

  call_open_interests = options_chain.calls.openInterest.tolist()
  call_strikes = options_chain.calls.strike.tolist()

  put_open_interests = options_chain.puts.openInterest.tolist()
  put_strikes = options_chain.puts.strike.tolist()

  calls = pd.DataFrame({'strikes':call_strikes,
                      'call_open_interests':call_open_interests}).set_index('strikes')
  puts = pd.DataFrame({'strikes':put_strikes,
                        'call_open_interests':put_open_interests}).set_index('strikes')
  
  options_df = pd.DataFrame()
  options_df['Calls'] = calls.copy()
  options_df['Puts'] = puts.copy()
  options_df = options_df.reset_index().fillna(0) #.astype('int')
  options_df =  options_df.set_index('strikes')
  return options_df


###### Input and get Ticker data ######
with st.sidebar:
  st.markdown(
    '''
    # Historical and Implied Earnings Positioning    
    ''')
  st.markdown('')
  
  with st.form(key='ticker_input'):
    stock_ticker_input = st.text_input(label='👇 Input Stock Ticker', value='None')
    submit_button = st.form_submit_button(label='Submit')
  
  st.markdown(
    '''
    Stock earnings announcement are considered a *binary event* which typically catalyzes explosive moves that are atypical from a stock's typical day to day movement. This dashboard helps examine historical movements after earnings and options positioning to help assist in putting on profitable positions.

    Enter the ticker for a stock with upcoming earnings and this app will examine the before and after %change after an earnings announcement. Additionally, this app scans the forward-looking options chain for large open interest positions that can act as strong lines of support and resistance.
    
    ---

    For a link of upcoming earnings, please check 
    🔗 [investing.com/earnings-calendar](https://www.investing.com/earnings-calendar/)
    ''')
  
try:

  ###### Input and get Ticker data ######
  try:
    raw_data = get_earnings_data(stock_ticker_input)
    stock_data = raw_data[0].set_index('Date')
    stock_data.index = pd.to_datetime(stock_data.index)
    earnings_data = raw_data[1]
    company_name = '$'+stock_ticker_input.upper()
    st.markdown('##### 🟢 Successfully obtained earnings information and options positioning data for ' + company_name)
    st.markdown('---')
    
  except:
    i = None

  earnings_column, options_column = st.columns(2)

  with earnings_column:
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

      low_7D = stock_data['Close'].iloc[-1] * (1 - earnings_data['+7D %Change'].std()/100)
      high_7D = stock_data['Close'].iloc[-1] * (1 + earnings_data['+7D %Change'].std()/100)

      col1, col2, col3 = st.columns([2,2,7])
      col1.metric(label='StDev 1D Move', value=str(std_1d_move)+'%', delta=None, delta_color="normal", help=None, label_visibility="visible")
      col2.metric(label='StDev 7D Move', value=str(std_7d_move)+'%', delta=std_delta_7d, delta_color="normal", help=None, label_visibility="visible")
      with col3:
        st.markdown('+1D historical expected range is \$' + str(round(low,2)) + ' - \$' + str(round(high,2)))
        st.markdown('+7D historical expected range is \$' + str(round(low_7D,2)) + ' - \$' + str(round(high_7D,2)))
    except:
      i = None

    ###### Display Candlestick ######
    try:
      candle_fig = go.Figure(data=go.Candlestick(x=stock_data[-100:].index,
                          open=stock_data[-100:]['Open'],
                          high=stock_data[-100:]['High'],
                          low=stock_data[-100:]['Low'],
                          close=stock_data[-100:]['Close']))
      candle_fig.add_hline(y=low, line_dash='dash', line_color='red', opacity=0.7, annotation_text=round(low,2), annotation_position='bottom right')
      candle_fig.add_hline(y=high, line_dash='dash', line_color='teal', opacity=0.7, annotation_text=round(high,2), annotation_position='top right')
      candle_fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_rangeslider_visible=False)
      candle_fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
      candle_fig.update_yaxes(title_text='Price')
      st.plotly_chart(candle_fig, use_container_width=True)

    except:
      i = None

    ###### Draw histograms #######
    #df_working = pd.DataFrame()

  with options_column:
    ##### Get options expiries list and put it in a selector dropdown #####
    try:
      options_expiries = get_options_expiries(stock_ticker_input)
      selected_options_expiry = st.selectbox('Available Options Expiries', options_expiries)
      st.markdown(' ')
      st.markdown(' ')
    except:
      i = None

    ##### Obtain options open interest data for this expiry #####
    try:
      options_data = get_options_open_interest(stock_ticker_input, selected_options_expiry)
      options_fig = go.Figure(data=[
        go.Bar(name='Puts', x=options_data.index, y=options_data['Puts']),
        go.Bar(name='Calls', x=options_data.index, y=options_data['Calls'])])
      options_fig.update_layout(barmode='stack', margin=dict(l=20, r=20, t=20, b=20), 
                                legend=dict(orientation="h", yanchor="bottom", y=0.85, xanchor="right", x=1),
                                yaxis={'side': 'right'})
      options_fig.update_xaxes(title_text='Strike Price')
      options_fig.update_yaxes(title_text='Open Interest')
      st.plotly_chart(options_fig, use_container_width=True)

    except:
      i = None
      st.text('No options expiry data for ' + selected_options_expiry)



  ###### Display Data Table ######
  st.markdown('---')
  data_col, spacer = st.columns(2)
  with data_col:
    try:
      with st.expander('Historical Earnings Data'):
        st.table(data=earnings_data.round(2))

      with st.expander('Options open Interest for ' + selected_options_expiry):
        st.table(options_data)    
    except:
      i = None

except:
  st.text('🟡 Enter a valid ticker symbol to obtain data')
