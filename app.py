import streamlit as st
import pandas as pd
import geopandas as gpd
import datetime
from datetime import date,datetime
import altair as alt
import plotly.express as px
import pydeck as pdk
import fiona

# -------------------------------------------------------
st.set_page_config(
    page_title="Amterdam woon[plaan",
    page_icon="🏠",
    layout="wide",
)


# -------------------------------------------------------
# @st.cache_data() 
# def get_data():
#     df_raw = gpd.read_file('https://maps.amsterdam.nl/open_geodata/geojson_lnglat.php?KAARTLAAG=WONINGBOUWPLANNEN&THEMA=woningbouwplannen')
#     df_raw = df_raw[df_raw.Start_bouw!=0]
#     return df_raw


# -------------------------------------------------------
# df = get_data()
df  = gpd.GeoDataFrame.from_features("data.geojson")


# -------------------------------------------------------
sidebar = st.sidebar
row_1_1,row_1_2 = st.columns([3,2], gap="large")
row_1_2_tab1, row_1_2_tab2 = row_1_2.tabs(["Pie-chart 🥧", "Sunburst-chart ☀️"])
"---"
row_2_1, row_2_2 = st.columns([3,1], gap="large")
"---"
row_3_1,row_3_2 = st.columns([1,6], gap="large")


# -------------------------------------------------------
filter_year = sidebar.slider("Kies jaarreeks", int(df.Start_bouw.min()), int(df.Start_bouw.max()), 
                    value=(int(df.Start_bouw.min()),
                           int(df.Start_bouw.max()))
                   )
filter_fase = sidebar.multiselect('Kies wat voor soort bouwfase',('Investeringsbesluit genomen','In aanbouw genomen','Verkenning','Principebesluit genomen'),
                                   default=('Investeringsbesluit genomen','In aanbouw genomen','Verkenning','Principebesluit genomen'))
filter_genre = sidebar.radio("",('Totaal','Stadsdeel', 'Gebied'), horizontal=True, label_visibility="collapsed")
filter_normilize = row_2_2.selectbox("", ('zero', 'normalize'), label_visibility="collapsed") 
filter_huur = row_3_1.selectbox('Kies wat voor soort huur',('Dure_huur','Sociale_huur','Middeldure_huur', 'Dure_huur_of_Koop','Koop'))
filter_map = row_3_1.selectbox('',('road', 'light_no_labels', 'dark_no_labels'),label_visibility="collapsed")


# -------------------------------------------------------    
choices_StartBouw = (df.Start_bouw>=filter_year[0]) & (df.Start_bouw<=filter_year[1])
choices_fase = (df.Fase.isin(filter_fase))
df_filter = df[choices_StartBouw & choices_fase]
        
   
if filter_genre == 'Totaal':

    #-------------------------
    df_total = df_filter[['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop']].sum().reset_index().rename(columns={0:"Antaal","index":"Huur"})
    
    #-------------------------
    df_table = df_total.set_index("Huur")
    
    #-------------------------
    df_piechart = df_total
    
    pie_theta = "Antaal"
    pie_radius = "Antaal"
    pie_color = "Huur"
    
    #-------------------------
    df_timeseries = pd.melt(df_filter, id_vars=['Start_bouw'], 
           value_vars=['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop']) 
    #-------------------------
    df_metrics = df_filter.groupby("Start_bouw")[['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop']].sum()

    #-------------------------
    df_map = df_filter
    
    #-------------------------
    df_sunburst = pd.melt(df_filter, id_vars= ['Start_bouw',"Fase","Stadsdeel"], 
                          value_vars=['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'])  
    path=['Start_bouw',"Fase","variable","Stadsdeel"]
    df_sunburst = df_sunburst.groupby(path,as_index=False).sum()
    
       
else:

    df_else = df_filter.groupby(filter_genre)[['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop']].sum()
    filter_rent = sidebar.selectbox('Kies een stadsdeel of gebied', df_else.index)
    
    #-------------------------
    df_table = df_else.style \
        .apply(lambda x: ['background-color: red' if x.name == filter_rent else '' for i in x],axis=1) \
        .apply(lambda x: ["color: white" if x.name == filter_rent else '' for i in x],axis=1) \
        .apply(lambda x: ["font-weight: bold" if x.name == filter_rent else '' for i in x],axis=1)
    
    #-------------------------
    df_piechart = df_else.T.reset_index()[["index",filter_rent]].rename(columns={"index":"Huur"})
    
    pie_theta = filter_rent
    pie_radius = filter_rent
    pie_color = "Huur"
    
    #-------------------------
    df_timeseries = pd.melt(df_filter[df_filter[filter_genre]==filter_rent], id_vars=['Start_bouw'], 
                       value_vars=['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'])
    
    #-------------------------
    df_metrics = df_filter[df_filter[filter_genre]==filter_rent].groupby("Start_bouw")[['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop']].sum()
    
    #-------------------------
    df_map = df_filter[df_filter[filter_genre]==filter_rent]
    
    #-------------------------
    df_sunburst = pd.melt(df_filter[df_filter[filter_genre]==filter_rent],
                          id_vars= ['Start_bouw',"Fase"], 
                          value_vars=['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'])  
    path=['Start_bouw',"Fase","variable"]
    df_sunburst = df_sunburst.groupby(path,as_index=False).sum()
        
   
# -------------------------------------------------------    
chart_pie = alt.Chart(df_piechart).encode(
    theta=alt.Theta(pie_theta, stack=True),
    radius=alt.Radius(pie_radius, scale=alt.Scale(type="sqrt", zero=True, rangeMin=0)),
    color=alt.Color(pie_color,scale=alt.Scale(scheme='category20b'),legend=alt.Legend(orient="left",title=None)),
).mark_arc(innerRadius=5, stroke="#fff")


# -------------------------------------------------------    
chart_timeseries = alt.Chart(df_timeseries).mark_bar(opacity=0.7
    ).encode(
    alt.X('Start_bouw:O', axis=alt.Axis(domain=False, tickSize=0),title="Start bouw"),
    alt.Y('sum(value):Q', stack=filter_normilize, title="Antaal"),
    alt.Color('variable:N',scale=alt.Scale(scheme='category20b'),legend=alt.Legend(orient="top",title=None)),
    ).properties(height=650, width=750)

   
#-------------------------
dict_metrics = {}
for i in df_metrics.columns:
    dict_metrics[i] = {"Highest":{"year":df_metrics.loc[df_metrics[i]==df_metrics[i].max()].index[0],
                                  "ammount":df_metrics[i].max()},
                       "Lowest":{"year":df_metrics.loc[df_metrics[i]==df_metrics[i].min()].index[0], 
                                 "ammount":df_metrics[i].min()}
                        }

text_Sociale_huur  = f"""
Sociale huur \n
Het hoogste jaar was **:green[{dict_metrics['Sociale_huur']['Highest']['year']}]** ({dict_metrics['Sociale_huur']['Highest']['ammount']}) en het laagste jaar was **:red[{dict_metrics['Sociale_huur']['Lowest']['year']}]** ({dict_metrics['Sociale_huur']['Lowest']['ammount']})
"""

text_Middeldure_huur  = f"""
Middeldure huur \n
Het hoogste jaar was **:green[{dict_metrics['Middeldure_huur']['Highest']['year']}]** ({dict_metrics['Middeldure_huur']['Highest']['ammount']}) en het laagste jaar was **:red[{dict_metrics['Middeldure_huur']['Lowest']['year']}]** ({dict_metrics['Middeldure_huur']['Lowest']['ammount']})
"""

text_Dure_huur  = f"""
Dure huur \n
Het hoogste jaar was **:green[{dict_metrics['Dure_huur']['Highest']['year']}]** ({dict_metrics['Dure_huur']['Highest']['ammount']}) en het laagste jaar was **:red[{dict_metrics['Dure_huur']['Lowest']['year']}]** ({dict_metrics['Dure_huur']['Lowest']['ammount']})
"""

text_Dure_huur_of_Koop  = f"""
Dure huur of Koop \n
Het hoogste jaar was **:green[{dict_metrics['Dure_huur_of_Koop']['Highest']['year']}]** ({dict_metrics['Dure_huur_of_Koop']['Highest']['ammount']}) en het laagste jaar was **:red[{dict_metrics['Dure_huur_of_Koop']['Lowest']['year']}]** ({dict_metrics['Dure_huur_of_Koop']['Lowest']['ammount']})
"""

text_Koop  = f"""
Koop huur \n
Het hoogste jaar was **:green[{dict_metrics['Koop']['Highest']['year']}]** ({dict_metrics['Koop']['Highest']['ammount']}) en het laagste jaar was **:red[{dict_metrics['Koop']['Lowest']['year']}]** ({dict_metrics['Koop']['Lowest']['ammount']})
"""


#-------------------------
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

BREAKS = [(df_map[filter_huur].max()*1)/6,
          (df_map[filter_huur].max()*2)/6,
          (df_map[filter_huur].max()*3)/6,
          (df_map[filter_huur].max()*4)/6,
          (df_map[filter_huur].max()*5)/6,
          df_map[filter_huur].max()/6,]


def color_scale(val):
    for i, b in enumerate(BREAKS):
        if val < b:
            return COLOR_RANGE[i]
    return COLOR_RANGE[i]

df_map["color"] = df_map[filter_huur].apply(lambda x: color_scale(x))

polygon_layer = pdk.Layer(
    'GeoJsonLayer',
    df_map,
    opacity=0.6,
    stroked=True,
    filled=True,
    extruded=True,
    wireframe=True,
    get_elevation=filter_huur,
    get_fill_color='color',
    get_line_color=[255, 255, 255],
    pickable=True
)

if filter_huur == 'Sociale_huur':
    tooltip = {"text": "Projectnaam: {Projectnaam} \n Start bouw: {Start_bouw} \n Antaal: {Sociale_huur}"}
elif filter_huur == 'Dure_huur':
    tooltip = {"text": "Projectnaam: {Projectnaam} \n Start bouw: {Start_bouw} \n Antaal: {Dure_huur}"}
elif filter_huur == 'Middeldure_huur':
    tooltip = {"text": "Projectnaam: {Projectnaam} \n Start bouw: {Start_bouw} \n Antaal: {Middeldure_huur}"}
elif filter_huur == 'Dure_huur_of_Koop':
    tooltip = {"text": "Projectnaam: {Projectnaam} \n Start bouw: {Start_bouw} \n Antaal: {Dure_huur_of_Koop}"}
elif filter_huur == 'Koop':
    tooltip = {"text": "Projectnaam: {Projectnaam} \n Start bouw: {Start_bouw} \n Antaal: {Koop}"}


r = pdk.Deck(
    [polygon_layer],
    tooltip = tooltip,
    map_style = filter_map,
    initial_view_state=INITIAL_VIEW_STATE,
)

    
#--------------------------------------------------
chart_sunburst = px.sunburst(df_sunburst, path=path, values='value',
                  labels={"value": "Antaal"}
                 )


#--------------------------------------------------
row_1_1.dataframe(df_table,use_container_width=True)
row_1_2_tab1.altair_chart((chart_pie),use_container_width=True)
row_1_2_tab2.plotly_chart(chart_sunburst, theme="streamlit", use_container_width=True)
row_2_1.altair_chart((chart_timeseries),use_container_width=True)
with row_2_2:
    st.subheader(text_Sociale_huur)
    st.subheader(text_Middeldure_huur)
    st.subheader(text_Dure_huur)
    st.subheader(text_Dure_huur_of_Koop)
    st.subheader(text_Koop)
row_3_2.pydeck_chart(pydeck_obj=r, use_container_width=True)
