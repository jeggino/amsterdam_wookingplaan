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
    page_icon="🌍",
    layout="wide",
    
)


# -------------------------------------------------------
@st.cache_data()  # 👈 Set the parameter
def get_data():
    df_raw = gpd.read_file('https://maps.amsterdam.nl/open_geodata/geojson_lnglat.php?KAARTLAAG=WONINGBOUWPLANNEN&THEMA=woningbouwplannen')
    df_raw = df_raw[df_raw.Start_bouw!=0]
    return df_raw

df = get_data()


# -------------------------------------------------------
with st.sidebar:
    filter_year = st.slider("Kies jaarreeks", int(df.Start_bouw.min()), int(df.Start_bouw.max()), 
                        value=(int(df.Start_bouw.min()),
                               int(df.Start_bouw.max()))
                       )
    filter_fase = st.multiselect('Kies wat voor soort bouwfase',['Investeringsbesluit genomen','In aanbouw genomen','Verkenning','Principebesluit genomen'])
    

# -------------------------------------------------------
choices_bouw = (df.Start_bouw>=filter_year[0]) & (df.Start_bouw<=filter_year[1])
choices_fase = (df.Fase.isin(filter_fase))
df_filter = df[choices_bouw & choices_fase]

# with st.sidebar:

left, right = st.columns([3,2])

with left:
    with st.container():
        df_segmentation = df_filter.groupby("Gebied")['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'].sum()
        
        #----------------------------------
        st.dataframe(df_segmentation,use_container_width=True)
        
        #----------------------------------
        filter_rent = st.selectbox('Kies een gebied',['Oud-Noord', 'Centrum-West', 'Noord-Oost', 'Buitenveldert, Zuidas','Geuzenveld, Slotermeer', 'IJburg, Zeeburgereiland','De Pijp, Rivierenbuurt', 'Osdorp', 'Oud-Zuid', 'Slotervaart','Oud-West, De Baarsjes', 'Oud-Oost','Indische Buurt, Oostelijk Havengebied', 'Watergraafsmeer','Centrum-Oost', 'Bijlmer-Centrum', 'Bos en Lommer', 'Noord-West','De Aker, Sloten, Nieuw-Sloten', 'Westerpark', 'Ouder-Amstel','Bijlmer-West', 'Sloterdijk Nieuw-West', 'Gaasperdam','Bijlmer-Oost', 'Weesp, Driemond'])
        source = df_segmentation.T[filter_rent].reset_index()

        base = alt.Chart(source).encode(
            theta=alt.Theta(f"filter_rent:Q", stack=True),
            radius=alt.Radius(filter_rent, scale=alt.Scale(type="sqrt", zero=True, rangeMin=20)),
            color="Gebied:N",
        )

        c1 = base.mark_arc(innerRadius=20, stroke="#fff")

        c2 = base.mark_text(radiusOffset=10).encode(text=f"filter_rent:Q")

        st.altair_chart((c1 + c2))


# -------------------------------------------------------
with right:
    with st.container():

        filter_rent = st.selectbox('Kies wat voor soort huur',('Dure_huur','Sociale_huur','Middeldure_huur', 'Dure_huur_of_Koop','Koop'))

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

        BREAKS = [(df_filter[filter_rent].max()*1)/6,
                  (df_filter[filter_rent].max()*2)/6,
                  (df_filter[filter_rent].max()*3)/6,
                  (df_filter[filter_rent].max()*4)/6,
                  (df_filter[filter_rent].max()*5)/6,
                  df_filter[filter_rent].max()/6,]


        def color_scale(val):
            for i, b in enumerate(BREAKS):
                if val < b:
                    return COLOR_RANGE[i]
            return COLOR_RANGE[i]

        df_filter["color"] = df_filter[filter_rent].apply(lambda x: color_scale(x))

        polygon_layer = pdk.Layer(
            'GeoJsonLayer',
            df_filter,
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

        r = pdk.Deck(
            [polygon_layer],
            tooltip = {"text": f"Number of {filter_rent}: {filter_rent}"},
            map_style = "light",
            initial_view_state=INITIAL_VIEW_STATE,
        )

        st.pydeck_chart(pydeck_obj=r, use_container_width=True)
