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

st.set_page_config(
    page_title="Amterdam woon[plaan",
    page_icon="🌍",
    layout="wide",
    
)


@st.cache_data()  # 👈 Set the parameter
def get_data():
    df_raw = gpd.read_file('https://maps.amsterdam.nl/open_geodata/geojson_lnglat.php?KAARTLAAG=WONINGBOUWPLANNEN&THEMA=woningbouwplannen')
    df_raw = df_raw[df_raw.Start_bouw!=0]
    return df_raw

df = get_data()

with st.sidebar:
    appointment = st.slider("Schedule your appointment:", int(df.Start_bouw.min()), int(df.Start_bouw.max()), value=(int(df.Start_bouw.min()),
                                                                                                                     int(df.Start_bouw.max())
                                                                                                                    ))
    filter_ = st.selectbox('How would you like to be contacted?',('Dure_huur','Sociale_huur','Middeldure_huur', 'Dure_huur_of_Koop','Koop'))
    


df_filter = df[(df.Start_bouw>=appointment[0]) & (df.Start_bouw<=appointment[1])]

# with st.sidebar:
df_segmentation = df_filter.groupby("Gebied")['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'].sum()
st.dataframe(df_segmentation)


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

BREAKS = [(df_filter[filter_].max()*1)/6,
          (df_filter[filter_].max()*2)/6,
          (df_filter[filter_].max()*3)/6,
          (df_filter[filter_].max()*4)/6,
          (df_filter[filter_].max()*5)/6,
          df_filter[filter_].max()/6,]


def color_scale(val):
    for i, b in enumerate(BREAKS):
        if val < b:
            return COLOR_RANGE[i]
    return COLOR_RANGE[i]

df_filter["color"] = df_filter[filter_].apply(lambda x: color_scale(x))

polygon_layer = pdk.Layer(
    'GeoJsonLayer',
    df_filter,
    opacity=0.6,
    stroked=True,
    filled=True,
    extruded=True,
    wireframe=True,
    get_elevation=filter_,
    get_fill_color='color',
    get_line_color=[255, 255, 255],
    pickable=True
)


r = pdk.Deck(
    [polygon_layer],
    tooltip = {"text": "Number of: {Sociale_huur}"},
    map_style = "light",
    initial_view_state=INITIAL_VIEW_STATE,
)

st.pydeck_chart(pydeck_obj=r, use_container_width=True)

#-----
df_filter_2 = df_filter[[filter_,"geometry"]]
a = df_filter_2.explore(filter_, 
              cmap="RdYlGn",
              k=5,
              tiles="CartoDB dark_matter",
              scheme="EqualInterval",
              legend_kwds={"colorbar":False,"caption":f"Number of {filter_}","fmt": "{:.0f}"},
             )
st_folium(a)
