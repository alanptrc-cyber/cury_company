# ================================
# Imports
# ================================
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import streamlit as st
from PIL import Image
from datetime import datetime

pio.renderers.default = "notebook"

st.set_page_config(page_title='Visão Entregadores' , page_icon='🚚', layout='wide')

# ================================
# Funções de dados
# ================================
def load_data(path):
    df = pd.read_csv(path)
    return df.copy()

def clean_data(df):
    for col in ['Delivery_person_Age', 'Road_traffic_density', 'City', 'Festival', 'multiple_deliveries']:
        df = df.loc[df[col] != 'NaN ', :].copy()

    df['Delivery_person_Age'] = df['Delivery_person_Age'].astype(int)
    df['Delivery_person_Ratings'] = df['Delivery_person_Ratings'].astype(float)
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')
    df['multiple_deliveries'] = df['multiple_deliveries'].astype(int)

    for col in ['ID', 'Road_traffic_density', 'Type_of_order', 'Type_of_vehicle', 'City', 'Festival']:
        df[col] = df[col].str.strip()

    df["Time_taken(min)"] = df["Time_taken(min)"].apply(lambda x: x.split("(min)")[1]).astype(int)

    return df


# ================================
# Funções de métricas
# ================================
def get_age_metrics(df):
    return df['Delivery_person_Age'].max(), df['Delivery_person_Age'].min()

def get_vehicle_condition_metrics(df):
    return df['Vehicle_condition'].max(), df['Vehicle_condition'].min()

def get_avg_ratings_per_deliver(df):
    return df.loc[:, ["Delivery_person_Ratings", "Delivery_person_ID"]].groupby("Delivery_person_ID").mean().reset_index()

def get_avg_ratings_by_traffic(df):
    df_aux = df.loc[:, ["Delivery_person_Ratings", "Road_traffic_density"]].groupby("Road_traffic_density").agg({"Delivery_person_Ratings": ["mean", "std"]})
    df_aux.columns = ["delivery_mean", "delivery_std"]
    return df_aux.reset_index()

def get_avg_ratings_by_weather(df):
    df_aux = df.loc[:, ["Delivery_person_Ratings", "Weatherconditions"]].groupby("Weatherconditions").agg({"Delivery_person_Ratings": ["mean", "std"]})
    df_aux.columns = ["delivery_mean", "delivery_std"]
    return df_aux.reset_index()

def get_top_fastest_deliverers(df):
    df2 = (df.loc[:, ['Delivery_person_ID', 'City', 'Time_taken(min)']]
             .groupby(['City', 'Delivery_person_ID'])
             .mean()
             .sort_values(['City', 'Time_taken(min)'], ascending=True)
             .reset_index())
    return pd.concat([
        df2.loc[df2['City'] == 'Metropolitian', :].head(10),
        df2.loc[df2['City'] == 'Urban', :].head(10),
        df2.loc[df2['City'] == 'Semi-Urban', :].head(10)
    ]).reset_index(drop=True)

def get_top_slowest_deliverers(df):
    df2 = (df.loc[:, ['Delivery_person_ID', 'City', 'Time_taken(min)']]
             .groupby(['City', 'Delivery_person_ID'])
             .mean()
             .sort_values(['City', 'Time_taken(min)'], ascending=False)
             .reset_index())
    return pd.concat([
        df2.loc[df2['City'] == 'Metropolitian', :].head(10),
        df2.loc[df2['City'] == 'Urban', :].head(10),
        df2.loc[df2['City'] == 'Semi-Urban', :].head(10)
    ]).reset_index(drop=True)


# ================================
# Função principal Streamlit
# ================================
def main():
    st.header('Marketplace - Visão Entregadores')

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

    # Layout
    tab1, _, _ = st.tabs(['Visão Gerencial', '_', '_'])

    with tab1:
        st.title('Overall Metrics')
        col1, col2, col3, col4 = st.columns(4, gap='large')

        maior_idade, menor_idade = get_age_metrics(df1)
        melhor_condicao, pior_condicao = get_vehicle_condition_metrics(df1)

        col1.metric('Maior idade', maior_idade)
        col2.metric('Menor idade', menor_idade)
        col3.metric('Melhor condição', melhor_condicao)
        col4.metric('Pior condição', pior_condicao)

        st.markdown("""---""")
        st.title('Avaliações')

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('##### Avaliação média por entregador')
            st.dataframe(get_avg_ratings_per_deliver(df1))
        with col2:
            st.markdown('##### Avaliação média por trânsito')
            st.dataframe(get_avg_ratings_by_traffic(df1))
            st.markdown('##### Avaliação média por clima')
            st.dataframe(get_avg_ratings_by_weather(df1))

        st.markdown("""---""")
        st.title('Velocidade de Entrega')

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('##### Top Entregadores mais rápidos')
            st.dataframe(get_top_fastest_deliverers(df1))
        with col2:
            st.markdown('##### Top Entregadores mais lentos')
            st.dataframe(get_top_slowest_deliverers(df1))


# ================================
# Execução
# ================================
if __name__ == "__main__":
    main()