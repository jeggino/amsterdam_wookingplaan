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

# -------------------------------------------------------
selected3 = option_menu(None, ["Grafieken", "Kaart"], 
    icons=['bi bi-pie-chart', 'bi bi-map'], 
    menu_icon="cast", default_index=0, orientation="horizontal")

# -------------------------------------------------------
df = get_data()

with st.sidebar:
    filter_year = st.slider("Kies jaarreeks", int(df.Start_bouw.min()), int(df.Start_bouw.max()), 
                        value=(int(df.Start_bouw.min()),
                               int(df.Start_bouw.max()))
                       )
    filter_fase = st.multiselect('Kies wat voor soort bouwfase',['Investeringsbesluit genomen','In aanbouw genomen','Verkenning','Principebesluit genomen'])
    
    choices_bouw = (df.Start_bouw>=filter_year[0]) & (df.Start_bouw<=filter_year[1])
    choices_fase = (df.Fase.isin(filter_fase))
    df_filter = df[choices_bouw & choices_fase]
        
if selected3 == "Grafieken":
    with st.container():
        genre = st.radio("What\'s your favorite movie genre",('Stadsdeel', 'Gebied'), horizontal=True)
        df_segmentation = df_filter.groupby(genre)['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'].sum()

        # -------------------------------------------------------
        tab1, tab2, tab3 = st.tabs(["📋", "bi bi-pie-chart", "Owl"])

        with tab1:
            st.dataframe(df_segmentation,use_container_width=True)

        with tab2:
            #----------------------------------
            filter_rent = st.selectbox('Kies een stadsdeel of gebied', df_segmentation.index)
            source = df_segmentation.T.reset_index()[["index",filter_rent]]

            base = alt.Chart(source).encode(
                theta=alt.Theta(filter_rent, stack=True),
                radius=alt.Radius(filter_rent, scale=alt.Scale(type="sqrt", zero=True, rangeMin=20)),
                color="index:N",
            )

            c1 = base.mark_arc(innerRadius=20, stroke="#fff")

            c2 = base.mark_text(radiusOffset=10).encode(text=filter_rent)

            st.altair_chart((c1 + c2),use_container_width=True)


elif selected3 == "Kaart":
    # -------------------------------------------------------
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
