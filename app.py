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
@st.cache_data()  # 👈 Set the parameter
def get_data():
    df_raw = gpd.read_file('https://maps.amsterdam.nl/open_geodata/geojson_lnglat.php?KAARTLAAG=WONINGBOUWPLANNEN&THEMA=woningbouwplannen')
    df_raw = df_raw[df_raw.Start_bouw!=0]
    return df_raw

# -------------------------------------------------------
selected3 = option_menu(None, ["Statistiek", "Kaart"], 
    icons=['bi bi-pie-chart', 'bi bi-map'], 
    menu_icon="cast", default_index=0, orientation="horizontal")

# -------------------------------------------------------
df = get_data()

col1, col2 = st.columns([2,7], gap="medium")

with col1:
    expander = st.expander("See explanation")
    filter_year = expander.slider("Kies jaarreeks", int(df.Start_bouw.min()), int(df.Start_bouw.max()), 
                        value=(int(df.Start_bouw.min()),
                               int(df.Start_bouw.max()))
                       )

    filter_fase = expander.multiselect('Kies wat voor soort bouwfase',['Investeringsbesluit genomen','In aanbouw genomen','Verkenning','Principebesluit genomen'],
                                default='Investeringsbesluit genomen')

    
choices_bouw = (df.Start_bouw>=filter_year[0]) & (df.Start_bouw<=filter_year[1])
choices_fase = (df.Fase.isin(filter_fase))
df_filter = df[choices_bouw & choices_fase]
        
if selected3 == "Statistiek":
   
    with col1:
        genre = expander.radio("",('Totaal','Stadsdeel', 'Gebied'), horizontal=True, label_visibility="collapsed")
        
    with col2:
        if genre == 'Totaal':
            st.write("ljfhbweslr")
        else:
            df_segmentation = df_filter.groupby(genre)['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'].sum()


            # -------------------------------------------------------
            tab1, tab2, tab3 = st.tabs(["📋", "📊", "🔢"])


            #-------------------------
            with st.container():
                with tab2:
                    #----------------------------------
                    left, right = st.columns([2,7],gap="small")

                    #----------------------------------
                    with left:
                        filter_rent = st.selectbox('Kies een stadsdeel of gebied', df_segmentation.index)

                    source = df_segmentation.T.reset_index()[["index",filter_rent]]

                    c1 = alt.Chart(source).encode(
                        theta=alt.Theta(filter_rent, stack=True),
                        radius=alt.Radius(filter_rent, scale=alt.Scale(type="sqrt", zero=True, rangeMin=20)),
                        color="index:N",
                    ).mark_arc(innerRadius=100, stroke="#fff")


                    #------------------------
                    source_2 = pd.melt(df_filter, id_vars=['Start_bouw'], 
                                       value_vars=['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'])   
                    source_2['Start_bouw'] = pd.to_datetime(source_2['Start_bouw'], format='%Y')


                    time_serie = alt.Chart(source_2).mark_area(
                        ).encode(
                        alt.X('Start_bouw:T',
                            axis=alt.Axis(format='%Y', domain=False, tickSize=0)
                        ),
                        alt.Y('sum(value):Q', stack='zero'),
                        alt.Color('variable:N',scale=alt.Scale(scheme='category20b')),
                        ).properties(height=250, width=750)


                    #------------------------
                    with right:
                        tab2_1, tab2_2 = st.tabs(["📋", "📊"])
                        with tab2_1:
                            st.altair_chart((c1),use_container_width=True)
                        with tab2_2:
                            st.altair_chart((time_serie),use_container_width=True)
        
            #----------------
            with st.container():
                with tab1:
                    st.dataframe(df_segmentation.style.format(precision=2).bar(color="orange"),use_container_width=True)


            #------------------------

            with tab3:
                list_1 = ['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop']
                df_metrics = df_filter.groupby("Start_bouw")['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'].sum()

                dict_metrics = {}
                for i in list_1:
                    dict_metrics[i] = {"Highest":{"year":df_metrics.loc[df_metrics[i]==df_metrics[i].max()].index[0],
                                            "ammount":df_metrics[i].max() },
                                 "Lowest":{"year":df_metrics.loc[df_metrics[i]==df_metrics[i].min()].index[0],
                                           "ammount":df_metrics[i].min()}
                                }  

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
            

elif selected3 == "Kaart":
    # -------------------------------------------------------
    
        
    with col1:
        filter_rent = st.selectbox('Kies wat voor soort huur',('Dure_huur','Sociale_huur','Middeldure_huur', 'Dure_huur_of_Koop','Koop'))
    
    with st.container():
        
        with col2:
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
#                 tooltip = {"text": f"Aantal: {filter_rent}"},
                map_style = "light",
                initial_view_state=INITIAL_VIEW_STATE,
            )

            st.pydeck_chart(pydeck_obj=r, use_container_width=True)
