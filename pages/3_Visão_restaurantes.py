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
from haversine import haversine
from datetime import datetime

pio.renderers.default = "notebook"

st.set_page_config(page_title='Visão Restaurantes' , page_icon='🍽️', layout='wide')

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
def get_unique_deliverers(df):
    return len(df['Delivery_person_ID'].unique())

def get_avg_distance(df):
    cols = ['Delivery_location_latitude', 'Delivery_location_longitude', 'Restaurant_latitude', 'Restaurant_longitude']
    df['distance'] = df.loc[:, cols].apply(lambda x: haversine((x['Restaurant_latitude'], x['Restaurant_longitude']),
                                                               (x['Delivery_location_latitude'], x['Delivery_location_longitude'])), axis=1)
    return np.round(df['distance'].mean(), 2)

def get_festival_metrics(df, festival_value, metric_type):
    df_aux = (df.loc[:, ['Time_taken(min)', 'Festival']]
                .groupby('Festival')
                .agg({'Time_taken(min)': ['mean', 'std']}))
    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()
    return np.round(df_aux.loc[df_aux['Festival'] == festival_value, metric_type], 2)

def get_avg_time_by_city(df):
    df_aux = (df.loc[:, ['City', 'Time_taken(min)']]
                .groupby('City')
                .agg({'Time_taken(min)': ['mean', 'std']}))
    df_aux.columns = ['avg_time', 'std_time']
    return df_aux.reset_index()

def get_order_distribution(df):
    df_aux = (df.loc[:, ['City', 'Time_taken(min)', 'Type_of_order']]
                .groupby(['City', 'Type_of_order'])
                .agg({'Time_taken(min)': ['mean', 'std']}))
    df_aux.columns = ['avg_time', 'std_time']
    return df_aux.reset_index()

def get_distance_distribution(df):
    cols = ['Delivery_location_latitude', 'Delivery_location_longitude', 'Restaurant_latitude', 'Restaurant_longitude']
    df['distance'] = df.loc[:, cols].apply(lambda x: haversine((x['Restaurant_latitude'], x['Restaurant_longitude']),
                                                               (x['Delivery_location_latitude'], x['Delivery_location_longitude'])), axis=1)
    avg_distance = df.loc[:, ['City', 'distance']].groupby('City').mean().reset_index()
    fig = go.Figure(data=[go.Pie(labels=avg_distance['City'], values=avg_distance['distance'], pull=[0, 0.1, 0])])
    return fig

def get_sunburst_time_distribution(df):
    df_aux = (df.loc[:, ['City', 'Time_taken(min)', 'Road_traffic_density']]
                .groupby(['City', 'Road_traffic_density'])
                .agg({'Time_taken(min)': ['mean', 'std']}))
    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()
    fig = px.sunburst(df_aux, path=['City', 'Road_traffic_density'], values='avg_time',
                      color='std_time', color_continuous_scale='RdBu',
                      color_continuous_midpoint=np.average(df_aux['std_time']))
    return fig


# ================================
# Função principal Streamlit
# ================================
def main():
    st.header('Marketplace - Visão Restaurantes')

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
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        col1.metric('Entregadores', get_unique_deliverers(df1))
        col2.metric('A distância Média', get_avg_distance(df1))
        col3.metric('Tempo Médio (Festival)', get_festival_metrics(df1, 'Yes', 'avg_time'))
        col4.metric('Desv.pd. Entrega (Festival)', get_festival_metrics(df1, 'Yes', 'std_time'))
        col5.metric('Tempo Médio (Sem Festival)', get_festival_metrics(df1, 'No', 'avg_time'))
        col6.metric('Desv.pd. Entrega (Sem Festival)', get_festival_metrics(df1, 'No', 'std_time'))

        st.markdown("""___""")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('###### Tempo médio de entrega por cidade')
            df_aux = get_avg_time_by_city(df1)
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Control', x=df_aux['City'], y=df_aux['avg_time'],
                                 error_y=dict(type='data', array=df_aux['std_time'])))
            fig.update_layout(barmode='group')
            st.plotly_chart(fig)

        with col2:
            st.markdown('###### Distribuição da Distância')
            st.dataframe(get_order_distribution(df1))

        st.markdown("""___""")
        st.title('Distribuição do Tempo')
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('###### Distância média dos restaurantes ao local de entrega')
            st.plotly_chart(get_distance_distribution(df1))
        with col2:
            st.markdown('###### Tempo médio e desv. pd. de entrega / cidade e tipo de tráfego')
            st.plotly_chart(get_sunburst_time_distribution(df1))


# ================================
# Execução
# ================================
if __name__ == "__main__":
    main()