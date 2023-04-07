import streamlit as st
from streamlit_option_menu import option_menu

import folium
from folium.plugins import Fullscreen,HeatMapWithTime,MiniMap,HeatMap
from streamlit_folium import st_folium,folium_static 

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

import datetime
from datetime import date,datetime

import altair as alt

import pydeck as pdk


# -------------------------------------------------------
st.set_page_config(
    page_title="Amterdam woon[plaan",
    page_icon="👷",
    layout="wide",
    
)


# -------------------------------------------------------
@st.cache_data() 
def get_data():
    df_raw = gpd.read_file('https://maps.amsterdam.nl/open_geodata/geojson_lnglat.php?KAARTLAAG=WONINGBOUWPLANNEN&THEMA=woningbouwplannen')
    df_raw = df_raw[df_raw.Start_bouw!=0]
    return df_raw


# -------------------------------------------------------
df = get_data()

expander = st.sidebar

filter_year = expander.slider("Kies jaarreeks", int(df.Start_bouw.min()), int(df.Start_bouw.max()), 
                    value=(int(df.Start_bouw.min()),
                           int(df.Start_bouw.max()))
                   )

filter_fase = expander.multiselect('Kies wat voor soort bouwfase',['Investeringsbesluit genomen','In aanbouw genomen','Verkenning','Principebesluit genomen'],
                                   default=['Investeringsbesluit genomen','In aanbouw genomen','Verkenning','Principebesluit genomen'])

    
choices_StartBouw = (df.Start_bouw>=filter_year[0]) & (df.Start_bouw<=filter_year[1])
choices_fase = (df.Fase.isin(filter_fase))

df_filter = df[choices_StartBouw & choices_fase]
        
   
genre = expander.radio("",('Totaal','Stadsdeel', 'Gebied'), horizontal=True, label_visibility="collapsed")
stack_filter = expander.selectbox("", ['zero', 'normalize'], label_visibility="collapsed") 

if genre == 'Totaal':

    df_total = df_filter[['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop']].sum().reset_index().rename(columns={0:"Antaal","index":"Huur"})
    #-------------------------

    pie_total = alt.Chart(df_total).encode(
        theta=alt.Theta("Antaal", stack=True),
        radius=alt.Radius("Antaal", scale=alt.Scale(type="sqrt", zero=True, rangeMin=5)),
        color=alt.Color('Huur:N',scale=alt.Scale(scheme='category20b')),
    ).mark_arc(innerRadius=20, stroke="#fff")
    #-------------------------

    source_2 = pd.melt(df_filter, id_vars=['Start_bouw'], 
           value_vars=['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'])   

    source_2['Start_bouw'] = pd.to_datetime(source_2['Start_bouw'], format='%Y')

    time_serie = alt.Chart(source_2).mark_area(
    ).encode(
    alt.X('Start_bouw:T',
        axis=alt.Axis(format='%Y', domain=False, tickSize=0)
    ),
    alt.Y('sum(value):Q', stack=stack_filter),
    alt.Color('variable:N',scale=alt.Scale(scheme='category20b'),legend=None),
    ).properties(height=250, width=750)
    #-------------------------
    
    list_1 = ['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop']
    df_metrics = df_filter.groupby("Start_bouw")['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'].sum()

    dict_metrics = {}
    for i in list_1:
        dict_metrics[i] = {"Highest":{"year":df_metrics.loc[df_metrics[i]==df_metrics[i].max()].index[0],
                                "ammount":df_metrics[i].max() },
                     "Lowest":{"year":df_metrics.loc[df_metrics[i]==df_metrics[i].min()].index[0],
                               "ammount":df_metrics[i].min()}
                    }  
    #-------------------------

    col2_left,col2_right = st.columns([2,5], gap="medium")

    col2_left.dataframe(df_total.set_index("Huur"),use_container_width=True)
    col2_right.altair_chart((pie_total),use_container_width=True)
    st.altair_chart((time_serie),use_container_width=True)
    
    tab3_col1, tab3_col2, tab3_col3 = st.columns(3) 
    tab3_col4, tab3_col5 = st.columns(2)
    tab3_col1.metric("Sociale_huur Highest", 
                     f"Jaar: {dict_metrics['Sociale_huur']['Highest']['year']}",
                     f"Antaal: {dict_metrics['Sociale_huur']['Highest']['ammount']}")
    tab3_col2.metric("Middeldure_huur Highest", 
                     f"Jaar: {dict_metrics['Middeldure_huur']['Highest']['year']}",
                     f"Antaal: {dict_metrics['Middeldure_huur']['Highest']['ammount']}")
    tab3_col3.metric("Dure_huur Highest", 
                     f"Jaar: {dict_metrics['Dure_huur']['Highest']['year']}",
                     f"Antaal: {dict_metrics['Dure_huur']['Highest']['ammount']}")
    tab3_col4.metric("Dure_huur_of_Koop Highest", 
                     f"Jaar: {dict_metrics['Dure_huur_of_Koop']['Highest']['year']}",
                     f"Antaal: {dict_metrics['Dure_huur_of_Koop']['Highest']['ammount']}")
    tab3_col5.metric("Koop Highest", 
                     f"Jaar: {dict_metrics['Koop']['Highest']['year']}",
                     f"Antaal: {dict_metrics['Koop']['Highest']['ammount']}")
    #-------------------------


else:

    df_segmentation = df_filter.groupby(genre)['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'].sum()
    filter_rent = expander.selectbox('Kies een stadsdeel of gebied', df_segmentation.index)
    #-------------------------

    source = df_segmentation.T.reset_index()[["index",filter_rent]]

    pie_subareas = alt.Chart(source).encode(
        theta=alt.Theta(filter_rent, stack=True),
        radius=alt.Radius(filter_rent, scale=alt.Scale(type="sqrt", zero=True, rangeMin=5)),
        color=alt.Color('index:N',scale=alt.Scale(scheme='category20b')),
    ).mark_arc(innerRadius=20, stroke="#fff")
    #-------------------------

    source_2 = pd.melt(df_filter[df_filter[genre]==filter_rent], id_vars=['Start_bouw'], 
                       value_vars=['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'])   
    source_2['Start_bouw'] = pd.to_datetime(source_2['Start_bouw'], format='%Y')

    time_serie = alt.Chart(source_2).mark_area(
        ).encode(
        alt.X('Start_bouw:T',
            axis=alt.Axis(format='%Y', domain=False, tickSize=0)
        ),
        alt.Y('sum(value):Q', stack=stack_filter),
        alt.Color('variable:N',scale=alt.Scale(scheme='category20b'),legend=None),
        ).properties(height=250, width=750)
    #-------------------------

    col2_left,col2_right = st.columns([5,3], gap="large")

    df_tab = df_segmentation.style \
        .apply(lambda x: ['background-color: red' if x.name == filter_rent else '' for i in x],axis=1) \
        .apply(lambda x: ["color: white" if x.name == filter_rent else '' for i in x],axis=1) \
        .apply(lambda x: ["font-weight: bold" if x.name == filter_rent else '' for i in x],axis=1)

    col2_left.dataframe(df_tab,use_container_width=True)
    col2_right.altair_chart((pie_subareas),use_container_width=True)
    st.altair_chart((time_serie),use_container_width=True)
    #-------------------------

#-------------------------
if genre == 'Totaal':
    df_map = df_filter
elif genre == 'Stadsdeel':
    df_map = df_filter[df_filter["Stadsdeel"]==filter_rent]
elif genre == 'Gebied':
    df_map = df_filter[df_filter["Gebied"]==filter_rent]


filter_rent = expander.selectbox('Kies wat voor soort huur',('Dure_huur','Sociale_huur','Middeldure_huur', 'Dure_huur_of_Koop','Koop'))
filter_map = expander.selectbox('',('road', 'light_no_labels', 'dark_no_labels'),label_visibility="collapsed")


INITIAL_VIEW_STATE = pdk.ViewState(
    latitude=52.374119, 
    longitude=4.895906,
    zoom=10,
    pitch=45,
    bearing=0
)

COLOR_RANGE = [
    [255, 255, 204],
    [254, 217, 118],
    [253, 141, 60],
    [128, 0, 38],
    [90, 0, 25],
    [50, 0, 15]
]

BREAKS = [(df_map[filter_rent].max()*1)/6,
          (df_map[filter_rent].max()*2)/6,
          (df_map[filter_rent].max()*3)/6,
          (df_map[filter_rent].max()*4)/6,
          (df_map[filter_rent].max()*5)/6,
          df_map[filter_rent].max()/6,]


def color_scale(val):
    for i, b in enumerate(BREAKS):
        if val < b:
            return COLOR_RANGE[i]
    return COLOR_RANGE[i]

df_map["color"] = df_map[filter_rent].apply(lambda x: color_scale(x))

polygon_layer = pdk.Layer(
    'GeoJsonLayer',
    df_map,
    opacity=0.6,
    stroked=True,
    filled=True,
    extruded=True,
    wireframe=True,
    get_elevation=filter_rent,
    get_fill_color='color',
    get_line_color=[255, 255, 255],
    pickable=True
)

if filter_rent == 'Sociale_huur':
    tooltip = {"text": "Antaal: {Sociale_huur}"}
elif filter_rent == 'Dure_huur':
    tooltip = {"text": "Antaal: {Dure_huur}"}
elif filter_rent == 'Middeldure_huur':
    tooltip = {"text": "Antaal: {Middeldure_huur}"}
elif filter_rent == 'Dure_huur_of_Koop':
    tooltip = {"text": "Antaal: {Dure_huur_of_Koop}"}
elif filter_rent == 'Koop':
    tooltip = {"text": "Antaal: {Koop}"}


r = pdk.Deck(
    [polygon_layer],
    tooltip = tooltip,
    map_style = filter_map,
    initial_view_state=INITIAL_VIEW_STATE,
)

st.pydeck_chart(pydeck_obj=r, use_container_width=True)
        





