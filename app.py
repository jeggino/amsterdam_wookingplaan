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
    appointment = st.slider("Schedule your appointment:", int(df.Start_bouw.min()), int(df.Start_bouw.max()), value=(int(df.Start_bouw.min()),
                                                                                                                     int(df.Start_bouw.max())
                                                                                                                    ))
    filter_ = st.selectbox('How would you like to be contacted?',('Dure_huur','Sociale_huur','Middeldure_huur', 'Dure_huur_of_Koop','Koop'))
    

# -------------------------------------------------------
df_filter = df[(df.Start_bouw>=appointment[0]) & (df.Start_bouw<=appointment[1])]

# with st.sidebar:
df_segmentation = df_filter.groupby("Gebied")['Sociale_huur', 'Middeldure_huur', 'Dure_huur', 'Dure_huur_of_Koop','Koop'].sum()
st.dataframe(df_segmentation)


# -------------------------------------------------------
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


# -------------------------------------------------------
# df_filter_2 = df_filter[[filter_,"geometry"]]
# a = df_filter_2.explore(filter_, 
#               cmap="RdYlGn",
#               k=5,
#               tiles="CartoDB dark_matter",
#               scheme="EqualInterval",
# #               legend_kwds={"colorbar":False,"caption":f"Number of {filter_}","fmt": "{:.0f}"},
#              )

# folium_static(a)


# -------------------------------------------------------
import pandas as pd
import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/Mining-BTC-180.csv")

for i, row in enumerate(df["Date"]):
    p = re.compile(" 00:00:00")
    datetime = p.split(df["Date"][i])[0]
    df.iloc[i, 1] = datetime

fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    specs=[[{"type": "table"}],
           [{"type": "scatter"}],
           [{"type": "scatter"}]]
)

fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=df["Mining-revenue-USD"],
        mode="lines",
        name="mining revenue"
    ),
    row=3, col=1
)

fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=df["Hash-rate"],
        mode="lines",
        name="hash-rate-TH/s"
    ),
    row=2, col=1
)

fig.add_trace(
    go.Table(
        header=dict(
            values=["Date", "Number<br>Transactions", "Output<br>Volume (BTC)",
                    "Market<br>Price", "Hash<br>Rate", "Cost per<br>trans-USD",
                    "Mining<br>Revenue-USD", "Trasaction<br>fees-BTC"],
            font=dict(size=10),
            align="left"
        ),
        cells=dict(
            values=[df[k].tolist() for k in df.columns[1:]],
            align = "left")
    ),
    row=1, col=1
)
fig.update_layout(
    height=800,
    showlegend=False,
    title_text="Bitcoin mining stats for 180 days",
)

st.pyplot(fig)
