import streamlit as st # web development
import numpy as np # np mean, np random 
import pandas as pd # read csv, df manipulation
import time # to simulate a real time data, time loop 
import plotly.express as px # interactive charts 
from plotly.subplots import make_subplots
from io import BytesIO, StringIO
from google.cloud import storage
from google.oauth2 import service_account
import plotly.graph_objects as go
import re
def get_byte_fileobj(project: str,
                     bucket: str,
                     path: str,
                     service_account_credentials_path: str = None) -> BytesIO:
    """
    Retrieve data from a given blob on Google Storage and pass it as a file object.
    :param path: path within the bucket
    :param project: name of the project
    :param bucket_name: name of the bucket
    :param service_account_credentials_path: path to credentials.
           TIP: can be stored as env variable, e.g. os.getenv('GOOGLE_APPLICATION_CREDENTIALS_DSPLATFORM')
    :return: file object (BytesIO)
    """
    blob = _get_blob(bucket, path, project, service_account_credentials_path)
    byte_stream = BytesIO()
    blob.download_to_file(byte_stream)
    byte_stream.seek(0)
    return byte_stream

def get_bytestring(project: str,
                   bucket: str,
                   path: str,
                   service_account_credentials_path: str = None) -> bytes:
    """
    Retrieve data from a given blob on Google Storage and pass it as a byte-string.
    :param path: path within the bucket
    :param project: name of the project
    :param bucket_name: name of the bucket
    :param service_account_credentials_path: path to credentials.
           TIP: can be stored as env variable, e.g. os.getenv('GOOGLE_APPLICATION_CREDENTIALS_DSPLATFORM')
    :return: byte-string (needs to be decoded)
    """
    blob = _get_blob(bucket, path, project, service_account_credentials_path)
    s = blob.download_as_string()
    return s


def _get_blob(bucket_name, path, project, service_account_credentials_path):
    credentials = service_account.Credentials.from_service_account_file(
        service_account_credentials_path) if service_account_credentials_path else None
    storage_client = storage.Client(project=project, credentials=credentials)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(path)
    return blob




st.set_page_config(
    page_title = 'Hedging Bot Statistics',
    page_icon = 'http://cryptoart.fund/wp-content/themes/cryptoart/assets/img/favicon/favicon-32x32.png',
    layout = 'wide'
)



# dashboard title

st.title("Hedging Bot v3 Statistics, CA")

# top-level filters 
files = []
path_to_private_key = '/defaust-343537e24181.json'
client = storage.Client.from_service_account_json(json_credentials_path=path_to_private_key)
for blob in client.list_blobs(bucket_or_name='hedging-bot-statistics'):
    files.append((blob.name))
#sdc
columns1, columns2, columns3, columns4 = st.columns(4)
with columns1:
    option = st.selectbox(
    'Choose position',
    (files))
with columns2:
    timeFrame = st.selectbox("Select TimeFrame", ['5s','20ms','10s','60s','5m','1h'])
with columns3:
    pattern = option.split('_')
    fin = re.findall(r'\d+',pattern[3])
    nft = (int(fin[0]))
    url = 'https://app.uniswap.org/#/pool/'+str(nft)
    st.markdown(f'''
<a href={url}><button style="background-color:Black;color:white;">Open NFT on Uniswap</button></a>
''',
    unsafe_allow_html=True)

def get_data():
    fileobj = get_byte_fileobj('defaust', 'hedging-bot-statistics', str(option), path_to_private_key)
    df1 = pd.read_csv(fileobj)
    return df1
get_data()

# creating a single-element container.
placeholder = st.empty()



apr_mapping = {'20ms' : 157784630, '5s' : 6311385.2, '10s' : 3155692.6, '60s' : 525948.7666666667, '5m' : 105189.7533333333, '1h' : 8765.8127777778}
while True:
    df = pd.DataFrame()
    df = df.join(get_data(), how = 'outer')
    df['Date'] = pd.to_datetime(df['Date'], format = '%Y-%m-%d %H:%M:%S.%f')
    df.set_index(df['Date'],inplace = True)
    df['Fees_in_risk_token_in_usd'] = df['Fees_in_risk_token'] * df['Price']
    initial_balance = ((df['Amount B'].iloc[0]) * (df['Price'].iloc[0]))+ (df['Amount A'].iloc[0]) #start balance for strategy
    
    df = df.groupby(pd.Grouper(key='Date', axis=0, freq=timeFrame, sort=True)).last().ffill()
    
   
   
    
    
    
    df['LP Balance'] = (df['Amount B'] * df['Price'] + df['Amount A']) #balance of LP in USD
    df['Pool PnL'] = df['LP Balance'] - initial_balance
    df['Pool PnL%'] = df['Pool PnL'] / initial_balance
    df['Short PnL'] = (df['Unrealized_PnL'] + df['Short_PNL']) #PnL of short position in USD
    df['Short PnL%'] = (df['Short PnL'] / initial_balance) #PnL of short position in %
    df['Funding_Fees_USD'] = (df['Funding_APR'] / apr_mapping[timeFrame]) * df['Total_Open_Short_Amount'] * df['Price']
    df['Funding_Fees_Agg_USD'] = (df['Funding_Fees_USD']).cumsum()
    df['Funding_Fees_Agg_percent'] = df['Funding_Fees_Agg_USD'] / initial_balance 
    
    df['Shorting_Fees_Agg_USD'] = df['Shorting_Fees']
    df['Shorting_Fees_Agg_percent'] = df['Shorting_Fees_Agg_USD'] / initial_balance
    df['Pool_Fees_Agg_USD'] = ((df['Fees_in_risk_token_in_usd']) + (df['Fees_in_stable_token']))
    df['Pool_Fees_Agg_percent'] = df['Pool_Fees_Agg_USD'] / initial_balance 
    df['Overall Return_usd'] = ((df['LP Balance']-initial_balance) + df['Short PnL'] + df['Pool_Fees_Agg_USD'] + df['Funding_Fees_Agg_USD'] + df['Shorting_Fees_Agg_USD'])
    df['Overall Return_%'] = (df['Overall Return_usd'] / initial_balance) * 100
    
    lp_value =  df['LP Balance'].iloc[-1] #current balance of LP in USD
    privious_lp_value = df['LP Balance'].iloc[-2]
    lp_pnl = lp_value - initial_balance #current PnL of LP position in USD
    short_pnl = df['Short PnL'].iloc[-1] #current PnL of short position in USD
    privious_short_pnl =  df['Short PnL'].iloc[-2] #privious PnL of short position in USD
    LP_Pnl_plus_Short_PnL = lp_pnl+short_pnl #Sum PnL of Short and LP
    privious_LP_Pnl_plus_Short_PnL = ((df['LP Balance'].iloc[-2]- initial_balance) + (df['LP Balance'].iloc[-2]- initial_balance))
    current_delta = df['Delta'].iloc[-1]
    privious_delta = df['Delta'].iloc[-2]
    
    
    
    with placeholder.container():
        pool_name, current_b, initial_b , a= st.columns(4)
        pool_name.metric(label = 'Chain', value = (df['Chain'].iloc[0]))
        initial_b.metric(label = 'Initial Balance', value = f"$ {round(initial_balance,2)}")
        current_b.metric(label = 'Balance', value = f"$ {round(df['Overall Return_usd'].iloc[-1] + initial_balance,2)} ", delta = f"$ {round((df['Overall Return_usd'].iloc[-1] + initial_balance) - initial_balance)}")
        a.metric(label="🔺 Delta", value=round(current_delta,4), delta= round(current_delta-privious_delta,4))
        # create three columns
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        # fill in those three columns with respective metrics or KPIs 
        kpi1.metric(label = 'Pool', value = df['Pool_Name'].iloc[0])
        kpi2.metric(label="🦄 LP Value $", value= f"$ {round(lp_value,2)} ", delta= round(lp_value-privious_lp_value,2))
        kpi3.metric(label="🤑 PnL Short ＄", value= f"$ {round(short_pnl,2)} ", delta= round(short_pnl - privious_short_pnl,2))
        kpi4.metric(label="💵 Short PnL + Pool PnL ＄", value= f"$ {round(LP_Pnl_plus_Short_PnL,2)} ", delta= round(LP_Pnl_plus_Short_PnL - privious_LP_Pnl_plus_Short_PnL,2))
        
        #if df['Price'].iloc[-1] > df['Price'].iloc[0]:
        #    color_price = 'green'
        #else: color_price = 'red'
        # create two columns for charts 
        
        fig_col0 = st.columns(1)
        st.markdown("### Overall Return")
        st.markdown("##### Pool PnL + Short PnL + Funding Fees + Pool Fees + Shorting Fees")
        
        fig0 = make_subplots(specs=[[{"secondary_y": True}]])
        fig0.update_layout(hovermode='x')
        fig0.add_trace(
            go.Scatter(x=df.index, y=df['Overall Return_usd'], name="in USD: "+str(round(df['Overall Return_usd'].iloc[-1],2))),
            secondary_y=False,)
        
        fig0.add_trace(
            go.Scatter(x=df.index, y=df['Overall Return_%'],name="in %: "+str(round(df['Overall Return_%'].iloc[-1],5))),
        secondary_y=True,)

        st.write(fig0)
        fig_col1, fig_col2 = st.columns(2)
        
        with fig_col1:
            st.markdown("### Price 🫣")
            st.markdown("##### Token Price")
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Price'], name="Price"),
                secondary_y=False,)
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Lower_Price'], name="Lower Range"),
                secondary_y=False,)
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Upper_Price'], name="Upper Range"),
                secondary_y=False,)
            
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Average_Open_Price'], name="Average Open Price"),
                secondary_y=False,)
            
            

            st.write(fig)
        with fig_col2:
            st.markdown("### Delta 🔺")
            st.markdown("##### Token in Pool - Tokens in Short")
            fig2 = px.line(data_frame = df, x = df.index, y = 'Delta')
            st.write(fig2)
            
        
        fig_col3, fig_col4 = st.columns(2)
        
        with fig_col3:
            st.markdown("### Pool & Short PnL, % ⚖️")
            st.markdown("##### PnL of Pool and Short positions without any fees")
            
            fig3 = go.Figure()
            fig3.add_trace(
                go.Scatter(x=df.index, y=df['Pool PnL%'], name="Pool PnL, %"))
            fig3.add_trace(
                go.Scatter(x=df.index, y=df['Short PnL%'], name="Short PnL, %"))
            fig3.add_trace(
                go.Scatter(x=df.index, y=(df['Short PnL%'] + df['Pool PnL%']), name="Sum PnL, %"))

            st.write(fig3)
        with fig_col4:
            st.markdown("### Fees Received and Paid, % 💎")
            st.markdown("##### Fees from Pool, Funding, Short, % on initial cap")
            fig4 = go.Figure()
            fig4.add_trace(
                go.Scatter(x=df.index, y=df['Pool_Fees_Agg_percent'] * 100, name="LP Fees, %"))
            fig4.add_trace(
                go.Scatter(x=df.index, y=df['Shorting_Fees_Agg_percent'] * 100, name="Shorting Fees, %"))
            fig4.add_trace(
                go.Scatter(x=df.index, y=df['Funding_Fees_Agg_percent'] * 100, name="Funding Fees, %"))
            fig4.add_trace(
                go.Scatter(x=df.index, y=(df['Pool_Fees_Agg_percent']*100 + df['Shorting_Fees_Agg_percent']*100 + df['Funding_Fees_Agg_percent']*100), name="Sum Fees, %"))
            
            st.write(fig4)
            
        fig_col5, fig_col6 = st.columns(2)
        
        with fig_col5:
            
            st.markdown("### Pool & Short PnL, USD ⚖️")
            
            fig5 = go.Figure()
            fig5.add_trace(
                go.Scatter(x=df.index, y=df['Pool PnL'], name="Pool PnL, USD"))
            fig5.add_trace(
                go.Scatter(x=df.index, y=df['Short PnL'], name="Short PnL, USD"))
            fig5.add_trace(
                go.Scatter(x=df.index, y=(df['Pool PnL'] + df['Short PnL']), name="Sum PnL, USD"))

            st.write(fig5)
        with fig_col6:
            st.markdown("### Fees Received and Paid, USD 💎")
            st.markdown("##### Fees from Pool, Funding, Short, USD")
            fig6 = go.Figure()
            fig6.add_trace(
                go.Scatter(x=df.index, y=df['Pool_Fees_Agg_USD'], name="LP Fees, USD"))
            fig6.add_trace(
                go.Scatter(x=df.index, y=df['Shorting_Fees_Agg_USD'], name="Shorting Fees, USD"))
            fig6.add_trace(
                go.Scatter(x=df.index, y=df['Funding_Fees_Agg_USD'], name="Funding Fees, USD"))
            fig6.add_trace(
                go.Scatter(x=df.index, y=(df['Pool_Fees_Agg_USD'] + df['Shorting_Fees_Agg_USD'] + df['Funding_Fees_Agg_USD']), name="Sum Fees, USD"))
            
            st.write(fig6)
        st.markdown("### Tokens in Pool VS Tokens in Short")
  
        fig7 = go.Figure()
        fig7.add_trace(
            go.Scatter(x=df.index, y=df['Amount B'], name="Amoun Tokens"))
        fig7.add_trace(
            go.Scatter(x=df.index, y=np.abs(df['Total_Open_Short_Amount']), name="Shorting Fees, USD"))
        
        st.write(fig7)
        st.markdown("### Detailed Data View")
        st.dataframe((df.tail(10)).sort_index(axis = 1))
    time.sleep(1)
    #placeholder.empty()


