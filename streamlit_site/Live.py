import pandas as pd
from datetime import timedelta
import streamlit as st
from PIL import Image
import matplotlib.pyplot as plt

image = Image.open('icon.png')

st.set_page_config(page_title="Cam stream Data - Live", 
                   page_icon=image, 
                   initial_sidebar_state="expanded",
                  layout="wide")

hide_streamlit_style = """
            <style>
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.sidebar.success("Select a page from above")

st.markdown("""
<style>
[data-testid="stDateInput"] [data-baseweb="input"]:before {
    content: url(https://i.imgur.com/pIZPHar.jpg) !important;
    padding-top: 8px !important;
    padding-left: 7px !important;
}
</style>
""", unsafe_allow_html=True)

st.header("Exploring Camera Stream Data")
st.text("This page allows you to delve into your Camstream data collected on various dates.")

@st.cache_data
def load_data(path):
  df = pd.read_excel(path)
  return df


def daily(date, data):
    df = pd.DataFrame(data)
    df['Hour'] = pd.to_datetime(df['time-stamp']).dt.hour

    filtered_df = df[df['time-stamp'].dt.date == pd.to_datetime(date).date()].drop(columns=["time-stamp"])

    daily_df = filtered_df.groupby('Hour', as_index=True).agg('sum')
    daily_df.reset_index(inplace=True)

    return daily_df, 'Hour'

def weekly(start_date, data):
    df = pd.DataFrame(data)
    df['time-stamp'] = pd.to_datetime(df['time-stamp'])
    df['Date'] = df['time-stamp'].dt.date
    filtered_df = df.loc[(df['Date'] >= pd.to_datetime(start_date).date()) & (df['Date'] < pd.to_datetime(start_date).date() + timedelta(days=7))].drop(columns=["time-stamp"])
    
    weekly_df = filtered_df.groupby('Date', as_index=True).agg('sum')
    weekly_df.reset_index(inplace=True)

    return weekly_df, 'Date'

file_path = 'count_result.xlsx'
data = load_data(file_path)

with st.expander("Data Preview"):
  st.dataframe(data, use_container_width=True, hide_index=True)

st.divider()

min_date = data['time-stamp'].min().date()
max_date = data['time-stamp'].max().date()
selected_date = st.date_input("Select Date", value=None, min_value=min_date, 
                              max_value=max_date, format="MM/DD/YYYY")

if selected_date is None:
   st.info("Select a Date", icon="ℹ")
   st.stop()

display_mode = st.radio('Select Display Mode', ['Daily', 'Weekly'])

if display_mode == 'Daily':
    result, x_label = daily(selected_date, data)
else:
    result, x_label = weekly(selected_date, data)

st.divider()
st.dataframe(result, use_container_width=True, hide_index=True)
st.divider()
st.bar_chart(result.set_index(result.columns[0]))

classes = data.columns[1:]

# Add a dropdown for selecting a class
selected_class = st.selectbox("Select an object from the list", classes)

fig, ax = plt.subplots()
if display_mode == 'Daily':
    ax.bar(result[x_label], result[selected_class])
    ax.set_xlabel(x_label)
    ax.set_xticks(result[x_label])
else:
    ax.bar(result['Date'], result[selected_class])
    ax.set_xlabel(x_label)
    # ax.set_xticks(result['Date'])

ax.set_ylabel(selected_class)
plt.xticks(rotation=45, ha='right')  
st.pyplot(fig)