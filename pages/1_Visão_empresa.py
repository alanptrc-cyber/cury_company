# ================================
# Imports
# ================================
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from PIL import Image
import folium
from streamlit_folium import folium_static
from haversine import haversine
from datetime import datetime

pio.renderers.default = "notebook"   # ou "browser"

st.set_page_config(page_title='Visão Empresa' , page_icon='📈', layout='wide')

# ================================
# Funções de limpeza de dados
# ================================
def load_data(path):
    df = pd.read_csv(path)
    return df.copy()

def clean_data(df):
    # Remove NaN
    for col in ['Delivery_person_Age', 'Road_traffic_density', 'City', 'Festival', 'multiple_deliveries']:
        df = df.loc[df[col] != 'NaN ', :].copy()

    # Conversões
    df['Delivery_person_Age'] = df['Delivery_person_Age'].astype(int)
    df['Delivery_person_Ratings'] = df['Delivery_person_Ratings'].astype(float)
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')
    df['multiple_deliveries'] = df['multiple_deliveries'].astype(int)

    # Remover espaços
    for col in ['ID', 'Road_traffic_density', 'Type_of_order', 'Type_of_vehicle', 'City', 'Festival']:
        df[col] = df[col].str.strip()

    # Limpar coluna de tempo
    df["Time_taken(min)"] = df["Time_taken(min)"].apply(lambda x: x.split("(min)")[1]).astype(int)

    return df


# ================================
# Funções de gráficos
# ================================
def plot_orders_by_day(df):
    df_aux = df.loc[:, ["ID", "Order_Date"]].groupby("Order_Date").count().reset_index()
    fig = px.bar(df_aux, x="Order_Date", y="ID")
    return fig

def plot_traffic_share(df):
    df_aux = df.loc[:, ["ID", "Road_traffic_density"]].groupby("Road_traffic_density").count().reset_index()
    df_aux = df_aux.loc[df_aux["Road_traffic_density"] != "NaN", :]
    df_aux["entregas_perc"] = df_aux["ID"] / df_aux["ID"].sum()
    fig = px.pie(df_aux, values="entregas_perc", names="Road_traffic_density")
    return fig

def plot_traffic_city(df):
    df_aux = df.loc[:, ["ID", "City", "Road_traffic_density"]].groupby(["City", "Road_traffic_density"]).count().reset_index()
    df_aux = df_aux.loc[(df_aux["City"] != "NaN") & (df_aux["Road_traffic_density"] != "NaN"), :]
    fig = px.scatter(df_aux, x="City", y="Road_traffic_density", size="ID", color="City")
    return fig

def plot_orders_by_week(df):
    df["week_of_year"] = df["Order_Date"].dt.strftime("%U")
    df_aux = df.loc[:, ["ID", "week_of_year"]].groupby("week_of_year").count().reset_index()
    fig = px.line(df_aux, x="week_of_year", y="ID")
    return fig

def plot_order_share_by_week(df):
    df["week_of_year"] = df["Order_Date"].dt.strftime("%U")
    df_aux1 = df.loc[:, ["ID", "week_of_year"]].groupby("week_of_year").count().reset_index()
    df_aux2 = df.loc[:, ["Delivery_person_ID", "week_of_year"]].groupby("week_of_year").nunique().reset_index()
    df_aux = pd.merge(df_aux1, df_aux2, how="inner")
    df_aux["order_by_deliver"] = df_aux["ID"] / df_aux["Delivery_person_ID"]
    fig = px.line(df_aux, x="week_of_year", y="order_by_deliver")
    return fig

def plot_map(df):
    columns = ['City','Road_traffic_density','Delivery_location_latitude','Delivery_location_longitude']
    data_plot = df.loc[:, columns].groupby(['City', 'Road_traffic_density']).median().reset_index()
    data_plot = data_plot.loc[(data_plot['City'] != 'NaN') & (data_plot['Road_traffic_density'] != 'NaN'), :]
    map_ = folium.Map(zoom_start=11)
    for _, location_info in data_plot.iterrows():
        popup_text = f"Cidade: {location_info['City']}<br>Tráfego: {location_info['Road_traffic_density']}"
        folium.Marker(
            location=[location_info['Delivery_location_latitude'], location_info['Delivery_location_longitude']],
            popup=popup_text
        ).add_to(map_)
    return map_


# ================================
# Função principal Streamlit
# ================================
def main():
    st.header('Marketplace - Visão Empresa')

    # Sidebar
    image = Image.open("cury_logo.png")
    st.sidebar.image(image, width=300)
    st.sidebar.markdown('# Cury Company')
    st.sidebar.markdown('## Fastest Delivery in Town')
    st.sidebar.markdown("""---""")

    data_slider = st.sidebar.slider('Até qual valor?',
        value=datetime(2022, 4, 13),
        min_value=datetime(2022, 2, 11),
        max_value=datetime(2022, 4, 6),
        format='DD-MM-YYYY')

    traffic_options = st.sidebar.multiselect('Quais as condições do trânsito',
        ['Low', 'Medium', 'High', 'Jam'],
        default=['Low', 'Medium', 'High', 'Jam'])

    st.sidebar.markdown("""---""")
    st.sidebar.markdown('### Developed by Alan Patricio')

    # Carregar e limpar dados
    df = load_data("dataset/train.csv")
    df1 = clean_data(df)

    # Aplicar filtros
    df1 = df1.loc[df1['Order_Date'] < data_slider, :]
    df1 = df1.loc[df1['Road_traffic_density'].isin(traffic_options), :]

    # Layout com abas
    tab1, tab2, tab3 = st.tabs(['Visão Gerencial', 'Visão Tática', 'Visão Geográfica'])

    with tab1:
        st.markdown('## Orders by day')
        st.plotly_chart(plot_orders_by_day(df1), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('## Traffic Order Share')
            st.plotly_chart(plot_traffic_share(df1), use_container_width=True)
        with col2:
            st.markdown('## Traffic Order City')
            st.plotly_chart(plot_traffic_city(df1), use_container_width=True)

    with tab2:
        st.markdown('# Order by Week')
        st.plotly_chart(plot_orders_by_week(df1), use_container_width=True)
        st.markdown('# Order Share by Week')
        st.plotly_chart(plot_order_share_by_week(df1), use_container_width=True)

    with tab3:
        st.markdown('# Country Maps')
        folium_static(plot_map(df1), width=1024, height=600)


# ================================
# Execução
# ================================
if __name__ == "__main__":
    main()
























































