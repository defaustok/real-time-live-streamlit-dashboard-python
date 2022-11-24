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
df = pd.read_csv("https://raw.githubusercontent.com/Lexie88rus/bank-marketing-analysis/master/bank.csv")
# read csv from a github repo
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

st.title("Hedging Bot Statistics, CA")

# top-level filters 

#job_filter = st.selectbox("Select the Job", pd.unique(df['job']))


# creating a single-element container.
placeholder = st.empty()

# dataframe filter 

#df = df[df['job']==job_filter]

# near real-time / live feed simulation 

while True: 
    fileobj = get_byte_fileobj('defaust', 'hedging-bot-statistics', 'stat.csv', 'defaust-343537e24181.json')
    df1 = pd.read_csv(fileobj)
    df1 = df1.drop(['Unnamed: 0.1','Unnamed: 0' ], axis = 1)
    
    df['age_new'] = df['age'] * np.random.choice(range(1,5))
    df['balance_new'] = df['balance'] * np.random.choice(range(1,5))

    # creating KPIs 
    avg_age = np.mean(df['age_new']) 
    
    initial_balance = (df1['Tokens_in_Pool'].iloc[0]*df1['Price'].iloc[0] * 2)
    count_married = int(df[(df["marital"]=='married')]['marital'].count() + np.random.choice(range(1,30)))
    df1['LP Balance'] = (df1['Tokens_in_Pool'] * df1['Price'] * 2)
    df1['Short PnL'] = df1['Unrealized_PnL_%'] * initial_balance
    lp_value = (df1['Tokens_in_Pool'].iloc[-1]*df1['Price'].iloc[-1] * 2)
    
    balance = lp_value
    short_pnl = df1['Unrealized_PnL_%'].iloc[-1] * initial_balance
    privious_short_pnl = ( df1['Unrealized_PnL_%'].iloc[-2] * initial_balance)
    roi_usd = df1['ROI'].iloc[-1] * initial_balance
    privious_roi_usd = df1['ROI'].iloc[-2] * initial_balance
    with placeholder.container():
        # create three columns
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        # fill in those three columns with respective metrics or KPIs 
        kpi1.metric(label="🔺 Delta", value=round(df1['Delta'].iloc[-1],4), delta= round(df1['Delta'].iloc[-1]-df1['Delta'].iloc[-2],4))
        kpi2.metric(label="🦄 LP Value $", value= f"$ {round(lp_value,2)} ", delta= round((df1['Tokens_in_Pool'].iloc[-1]*df1['Price'].iloc[-1] * 2)- (df1['Tokens_in_Pool'].iloc[-2]*df1['Price'].iloc[-2] * 2),2))
        kpi3.metric(label="🤑 PnL Short ＄", value= f"$ {round(short_pnl,2)} ", delta= round(short_pnl - privious_short_pnl,2))
        kpi4.metric(label="💵 Overall PnL ＄", value= f"$ {round(roi_usd,2)} ", delta= round(roi_usd - privious_roi_usd,2))

        #if df1['Price'].iloc[-1] > df1['Price'].iloc[0]:
        #    color_price = 'green'
        #else: color_price = 'red'
        # create two columns for charts 
        fig_col0 = st.columns(1)
        st.markdown("### Overall Balance")
        
        fig0 = make_subplots(specs=[[{"secondary_y": True}]])
        fig0.update_layout(hovermode='x')
        fig0.add_trace(
            go.Scatter(x=df1['Date'], y=(df1['LP Balance'] + df1['Short PnL']), name="USD"),
            secondary_y=False,)
        
        fig0.add_trace(
            go.Scatter(x=df1['Date'], y=((df1['LP Balance'] + df1['Short PnL'])/initial_balance-1), name="Change in %"),
        secondary_y=True,)

        st.write(fig0)
        fig_col1, fig_col2 = st.columns(2)
        
        with fig_col1:
            st.markdown("### Price & IL 🫣")
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(x=df1['Date'], y=df1['Price'], name="Price"),
                secondary_y=False,)
            
            fig.add_trace(
                go.Scatter(x=df1['Date'], y=df1['Impermanent_Loss'], name="IL"),
            secondary_y=True,)

            st.write(fig)
        with fig_col2:
            st.markdown("### Delta 🔺")
            fig2 = px.line(data_frame = df1, x = 'Date', y = 'Delta')
            st.write(fig2)
            
        
        fig_col3, fig_col4 = st.columns(2)
        
        with fig_col3:
            st.markdown("### Pool & Short PnL, % ⚖️")
            
            fig3 = go.Figure()
            fig3.add_trace(
                go.Scatter(x=df1['Date'], y=df1['Pool_Money'], name="Pool PnL, %"))
            fig3.add_trace(
                go.Scatter(x=df1['Date'], y=df1['Unrealized_PnL_%'], name="Short PnL, %"))
            fig3.add_trace(
                go.Scatter(x=df1['Date'], y=(df1['Unrealized_PnL_%'] + df1['Pool_Money']), name="Sum PnL, %"))

            st.write(fig3)
        with fig_col4:
            st.markdown("### ROI, % 💎")
            fig2 = px.line(data_frame = df1, x = 'Date', y = 'ROI')
            st.write(fig2)
            
        fig_col5, fig_col6 = st.columns(2)
        
        with fig_col5:
            
            st.markdown("### Pool & Short PnL, USD ⚖️")
            
            fig5 = go.Figure()
            fig5.add_trace(
                go.Scatter(x=df1['Date'], y=df1['Pool_Money'] * initial_balance, name="Pool PnL, USD"))
            fig5.add_trace(
                go.Scatter(x=df1['Date'], y=df1['Unrealized_PnL_%'] * initial_balance, name="Short PnL, USD"))
            fig5.add_trace(
                go.Scatter(x=df1['Date'], y=((df1['Unrealized_PnL_%'] + df1['Pool_Money'])*initial_balance), name="Sum PnL, USD"))

            st.write(fig5)
        with fig_col6:
            st.markdown("### ROI, USD 💎")
            fig6 = go.Figure()
            fig6.add_trace(
                go.Scatter(x=df1['Date'], y=df1['ROI'] * initial_balance, name="ROI, USD"))
            
            st.write(fig6)
        
        st.markdown("### Detailed Data View")
        st.dataframe((df1.tail(50)).sort_values(axis = 0, by = ['Date']))
    time.sleep(5)
    #placeholder.empty()


