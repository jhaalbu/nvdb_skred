import streamlit as st
import pandas as pd
import nvdbapiv3
import altair as alt
import geopandas as gpd
from shapely import wkt
import folium
import streamlit_folium
import xlsxwriter
from io import BytesIO

def skred_type_by_month(data_df):
    color_map = {
        'Stein': 'rgb(178,178,178)',
        'Is/stein': 'rgb(115,150,150)',
        'Jord/løsmasse': 'rgb(168,112,0)',
        'Flomskred (vann+stein+jord)': 'rgb(0,112,255)',
        'Is': 'rgb(115,255,223)',
        'Snø' : 'rgb(255,255,255)',
        'Sørpeskred (vann+snø+stein)' : 'rgb(201, 165, 117)',
    }
    month_mapping = {
        'January': 'Januar',
        'February': 'Februar',
        'March': 'Mars',
        'April': 'April',
        'May': 'Mai',
        'June': 'Juni',
        'July': 'Juli',
        'August': 'August',
        'September': 'September',
        'October': 'Oktober',
        'November': 'November',
        'December': 'Desember'
    }

    # Create a month column
    data_df['month'] = data_df['Skred_dato'].dt.strftime('%B')
    
    # Translate month names to Norwegian
    data_df['month'] = data_df['month'].map(month_mapping)

    # Group data by month and type and count occurrences
    data_grouped = data_df.groupby(['month', 'Type_skred']).size().reset_index(name='count')

    # Color mapping
    

    # Create the chart
    chart = alt.Chart(data_grouped).mark_bar().encode(
        x=alt.X('month:O', title='Måned', axis=alt.Axis(titleFont='Courier', titleFontSize=12, labelColor='white', titleColor='white', gridColor='#555555'), sort=list(month_mapping.values())),  # Use the Norwegian month names for sorting
        y=alt.Y('count:Q', title='Antall hendelser', axis=alt.Axis(titleFont='Courier', titleFontSize=12, labelColor='white', titleColor='white', gridColor='#555555'), stack=True),
        color=alt.Color('Type_skred:N', legend=alt.Legend(title="Skredtype"), scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values()))),
        tooltip=['month', 'Type_skred', 'count']
    ).properties(
        title={
        "text": 'Skredhendelser per måned',
        "fontSize": 16,
        "color": 'white',
        "anchor": 'middle',   # Centers the title
        "offset": 20          # Adds a bit more space around the title
        },
        padding={"top": 30} 
    ).configure(
        background='#333333'  # Dark background
    ).configure_title(
        fontSize=16,
        font='Courier',
        color='white'
    ).configure_legend(
        titleFontSize=12,
        labelFontSize=10,
        titleColor='white',
        labelColor='white'
    )

    return chart

def skred_type_counts(data_df):
    color_map = {
        'Stein': 'rgb(178,178,178)',
        'Is/stein': 'rgb(115,150,150)',
        'Jord/løsmasse': 'rgb(168,112,0)',
        'Flomskred (vann+stein+jord)': 'rgb(0,112,255)',
        'Is': 'rgb(115,255,223)',
        'Snø' : 'rgb(255,255,255)',
        'Sørpeskred (vann+snø+stein)' : 'rgb(201, 165, 117)',
    }

    # Aggregating the data
    skred_counts = data_df['Type_skred'].value_counts().reset_index()
    skred_counts.columns = ['Type_skred', 'count']

    # Main bar chart
    bars = alt.Chart(skred_counts).mark_bar().encode(
        x=alt.X('Type_skred:N', title='Skredtype', axis=alt.Axis(titleFont='Courier', titleFontSize=12, labelColor='white', titleColor='white', gridColor='#555555')),
        y=alt.Y('count:Q', title='Antall hendelser', axis=alt.Axis(titleFont='Courier', titleFontSize=12, labelColor='white', titleColor='white', gridColor='#555555')),
        color=alt.Color('Type_skred:N', legend=alt.Legend(title="Skredtype"), scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values()))),
        tooltip=['Type_skred', 'count']
    )

    # Text above bars
    text = bars.mark_text(
        align='center',
        baseline='bottom',
        dy=-10  # Adjust this value to shift the text's vertical position
    ).encode(
        text='count:Q'
    )

    chart = (bars + text).properties(
        title={
        "text": 'Skredhendelser per type',
        "fontSize": 16,
        "color": 'white',
        "anchor": 'middle',   # Centers the title
        "offset": 20          # Adds a bit more space around the title
        },
        padding={"top": 30}  
    ).configure(
        background='#333333'  # Dark background
    ).configure_title(
        fontSize=16,
        font='Courier',
        color='white'
    ).configure_legend(
        titleFontSize=12,
        labelFontSize=10,
        titleColor='white',
        labelColor='white'
    )
    
    return chart

def plot(data_df):
    color_map = {
        'Stein': 'rgb(178,178,178)',
        'Is/stein': 'rgb(115,150,150)',
        'Jord/løsmasse': 'rgb(168,112,0)',
        'Flomskred (vann+stein+jord)': 'rgb(0,112,255)',
        'Is': 'rgb(115,255,223)',
        'Snø' : 'rgb(255,255,255)',
        'Sørpeskred (vann+snø+stein)' : 'rgb(201, 165, 117)',}
    
    data = data_df.pivot_table(
        index=data_df.Skred_dato.dt.year,
        columns='Type_skred',
        aggfunc='size')
    #data = data.fillna(0)
    
    data_long = data.reset_index().melt(id_vars='Skred_dato', value_name='count', var_name='Type_skred')


    chart = alt.Chart(data_long).mark_bar().encode(
        x=alt.X('Skred_dato:O', title='År', axis=alt.Axis(titleFont='Courier', titleFontSize=12, labelColor='white', titleColor='white', gridColor='#555555')),
        y=alt.Y('count:Q', title='Antall hendelser', axis=alt.Axis(titleFont='Courier', titleFontSize=12, labelColor='white', titleColor='white', gridColor='#555555')),
        color=alt.Color('Type_skred:N', legend=alt.Legend(title="Skredtype"), scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values()))),
        tooltip=['Skred_dato', 'Type_skred', 'count']
    ).properties(
        title={
        "text": 'Skredhendelser',
        "fontSize": 16,
        "color": 'white',
        "anchor": 'middle',   # Centers the title
        "offset": 20          # Adds a bit more space around the title
        },
        padding={"top": 30} 
    ).configure(
        background='#333333'  # Dark background
    ).configure_title(
        fontSize=16,
        font='Courier',
        color='white'
    ).configure_legend(
        titleFontSize=12,
        labelFontSize=10,
        titleColor='white',
        labelColor='white'
    )
    return chart
#st.set_page_config(layout="wide")

def style_function(feature):
    color_map = {
    'Stein': '#b2b2b2',  # RGB converted to HEX
    'Is/stein': '#73ffdf',
    'Jord/løsmasse': '#a87000',
    'Flomskred (vann+stein+jord)': '#0070FF',
    'Is': '#73ffdf',
    'Snø': '#ffffff',
    'Sørpeskred (vann+snø+stein)': '#c9a575',
    }
    skred_type = feature['properties']['Type_skred']
    return {
        'color': color_map.get(skred_type, '#000000'),  # Default to black if no match
        'weight': 6  # Optional: Sets the thickness of the line
    }

def kart(df):
    df['geometry'] = df['geometri'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf.crs = "EPSG:32633"
    gdf_wgs84 = gdf.to_crs("EPSG:4326")
    for column in gdf_wgs84.columns:
        gdf_wgs84[column] = gdf_wgs84[column].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, pd.Timestamp) else x)


    middle_idx = len(gdf_wgs84) // 2
    linestring = gdf_wgs84.iloc[middle_idx]['geometry']

    midpoint = linestring.interpolate(0.5, normalized=True)
    #st.write(gdf)

    m = folium.Map(location=[midpoint.y, midpoint.x], zoom_start=10)  # Adjust latitude and longitude to center your map
    folium.TileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', 
                 name="CartoDB Dark Matter", 
                 attr="© OpenStreetMap contributors, © CartoDB").add_to(m)
    for _, row in gdf_wgs84.iterrows():
        geojson_row = gpd.GeoDataFrame([row]).to_json()
        folium.GeoJson(
            geojson_row,
            style_function=style_function
        ).add_to(m)
    return streamlit_folium.folium_static(m)

def last_ned_shape(skred):
    df = pd.DataFrame.from_records(skred.to_records())
    df_utvalg = df[['Skred dato', 'Type skred', 'Volum av skredmasser på veg', 
                    'Stedsangivelse', 'Værforhold på vegen', 'Blokkert veglengde', 
                    'geometri', 'vref']].copy() 

    df_utvalg.columns = df_utvalg.columns.str.replace(' ', '_')
    df['geometri'] = df['geometri'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf.crs = "EPSG:32633"
    return gdf

def create_point_map(df):
    # Convert 'geometri' column to GeoSeries
    df['geometry'] = df['geometri'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    # Set the coordinate system for the GeoDataFrame to UTM 33N
    gdf.crs = "EPSG:32633"

    # Transform to WGS 84
    gdf = gdf.to_crs("EPSG:4326")

    # Compute midpoints
    gdf['midtpunkt'] = gdf['geometry'].interpolate(0.5, normalized=True)

    # Determine center of the map
    center = gdf['midtpunkt'].unary_union.centroid
    m = folium.Map(location=[center.y, center.x], zoom_start=10)

    # Define colormap
    color_map = {
        'Stein': '#b2b2b2',
        'Is/stein': '#73ffdf',
        'Jord/løsmasse': '#a87000',
        'Flomskred (vann+stein+jord)': '#0070FF',
        'Is': '#73ffdf',
        'Snø': '#ffffff',
        'Sørpeskred (vann+snø+stein)': '#c9a575',
    }

    # Add midpoints to the map
    for _, row in gdf.iterrows():
        point_color = color_map.get(row['Type_skred'], '#000000')  # Default to black if not found
        folium.CircleMarker(
            location=[row['midtpunkt'].y, row['midtpunkt'].x],
            radius=5,
            color=point_color,
            fill=True,
            fill_opacity=0.6,
            popup=row['Skred_dato']  # This will show the Type_skred value when clicking on a point
        ).add_to(m)
    
    return m

def databehandling(skred):
    
    df = pd.DataFrame.from_records(skred.to_records())
    df_utvalg = df[['Skred dato', 'Type skred', 'Volum av skredmasser på veg', 
                    'Stedsangivelse', 'Værforhold på vegen', 'Blokkert veglengde', 
                    'geometri', 'vref']].copy() 

    df_utvalg.columns = df_utvalg.columns.str.replace(' ', '_')
    df_utvalg['Skred_dato'] = pd.to_datetime(df_utvalg['Skred_dato'], errors='coerce')

    return df_utvalg

def last_ned_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data

st.set_page_config(page_title='NVDB skreddata', page_icon=None, layout="centered", initial_sidebar_state="auto", menu_items=None)


st.title('NVDB skreddata')
st.write('Henter data fra NVDB api v3, ved nedhenting av fylker og heile landet tek det ein del tid å hente data')

utvalg = st.radio('Velg utaksmåte', ['Vegreferanse', 'Vegreferanse uvida', 'Landsdekkande', 'Fylke', 'Kontraktsområde'])

if utvalg == 'Fylke':
    st.write('OBS! Kan ta lang tid å hente data')
    fylke = st.selectbox(
    'Velg fylke',
    ('Agder', 'Innlandet', 'Møre og Romsdal', 'Nordland',  'Oslo', 'Rogaland', 'Troms og Finnmark', 'Trøndelag',  'Vestfold og Telemark', 'Vestland', 'Viken'))
    
    fylker = {
    "Agder": "42",
    "Innlandet": "34",
    "Møre og Romsdal": "15",
    "Nordland": "18",
    "Oslo": "03",
    "Rogaland": "11",
    "Troms og Finnmark": "54",
    "Trøndelag": "50",
    "Vestfold": "38",
    "Vestland": "46",
    "Viken": "30"
    }


    if st.button('Hent skreddata'):   
        skred = nvdbapiv3.nvdbFagdata(445)
        skred.filter({'fylke' : fylker[fylke]})

        df_utvalg = databehandling(skred)
        st.download_button(
            "Last ned skredpunkt",
            df_utvalg.to_csv().encode("utf-8"),
            "klimadata.csv",
            "text/csv",
            key="download-csv",
        )
        st.altair_chart(plot(df_utvalg), use_container_width=True)
        st.altair_chart(skred_type_counts(df_utvalg), use_container_width=True)
        st.altair_chart(skred_type_by_month(df_utvalg), use_container_width=True)

        kart(df_utvalg)

if utvalg == 'Landsdekkande':
    st.write('OBS! Tar lang tid å hente data')

    if st.button('Hent skreddata'):
        skred = nvdbapiv3.nvdbFagdata(445)

        df_utvalg = databehandling(skred)
        st.download_button(
            "Last ned skredpunkt",
            df_utvalg.to_csv().encode("utf-8"),
            "klimadata.csv",
            "text/csv",
            key="download-csv",
        )
        st.altair_chart(plot(df_utvalg), use_container_width=True)
        st.altair_chart(skred_type_counts(df_utvalg), use_container_width=True)
        st.altair_chart(skred_type_by_month(df_utvalg), use_container_width=True)
        kart(df_utvalg)

if utvalg == 'Vegreferanse':
    st.write('Kunn for heile vegstrekninger, eller heile vegklasser')
    st.write('Eksempel: Rv5, Fv53, Ev39')
    st.write('Det går og an å gi inn Rv, Ev, eller Fv for alle skred på vegklassene.')
    vegreferanse = st.text_input('Vegreferanse', 'Rv5')

    if st.button('Hent skreddata'):
    #try:
        skred = nvdbapiv3.nvdbFagdata(445)
        skred.filter({'vegsystemreferanse' : vegreferanse})

        df_utvalg = databehandling(skred)
        st.download_button(
            "Last ned skredpunkt",
            df_utvalg.to_csv().encode("utf-8"),
            "klimadata.csv",
            "text/csv",
            key="download-csv",
        )
        st.altair_chart(plot(df_utvalg), use_container_width=True)
        st.altair_chart(skred_type_counts(df_utvalg), use_container_width=True)
        st.altair_chart(skred_type_by_month(df_utvalg), use_container_width=True)

        streamlit_folium.folium_static(create_point_map(df_utvalg))


if utvalg == 'Vegreferanse uvida':
    
    vegnummer = st.text_input('Vegnummer', 'Rv5')
    col1, col2 = st.columns(2)
    with col1:
        delstrekning_fra = st.number_input('Delstrekning fra (S1D1 = 1)', 1)
        delstrekning_til = st.number_input('Delstrekning til (S8D1 = 8)', 8)
    with col2:
        meterverdi_fra = st.number_input('Meterverdi fra', 0)
        meterverdi_til = st.number_input('Meterverdi til', 20000)
    vegreferanse = f'{vegnummer}S{delstrekning_fra}-{delstrekning_til}'

    karttype = st.radio('Vis kart med linjer eller punkter', ['Punkter', 'Linjer'])

    if st.button('Hent skreddata'):
        #try:
        skred = nvdbapiv3.nvdbFagdata(445)
        skred.filter({'vegsystemreferanse' : vegreferanse})

        df_utvalg = databehandling(skred)
        
        # Extract segment as int
        df_utvalg['segment'] = df_utvalg['vref'].str.extract(r'S(\d+)D\d+').astype(int)
        df_utvalg[['start_distance', 'end_distance']] = df_utvalg['vref'].str.extract(r'm(\d+)-(\d+)')

        # Convert the extracted distances to int
        df_utvalg['start_distance'] = df_utvalg['start_distance'].astype(int)
        df_utvalg['end_distance'] = df_utvalg['end_distance'].astype(int)

        # Step 2: Data Filtering



        condition1 = (df_utvalg['segment'] == delstrekning_fra) & (df_utvalg['start_distance'] >= meterverdi_fra)
        condition2 = (df_utvalg['segment'] > delstrekning_fra) & (df_utvalg['segment'] < delstrekning_til)
        condition3 = (df_utvalg['segment'] == delstrekning_til) & (df_utvalg['end_distance'] <= meterverdi_til)

        filtered_df = df_utvalg[condition1 | condition2 | condition3]
        #st.write(filtered_df)
  
        st.download_button(
            "Last ned skredpunkt",
            filtered_df.to_csv().encode("utf-8"),
            "klimadata.csv",
            "text/csv",
            key="download-csv",
        )
        st.altair_chart(plot(filtered_df), use_container_width=True)
        st.altair_chart(skred_type_counts(filtered_df), use_container_width=True)
        st.altair_chart(skred_type_by_month(filtered_df), use_container_width=True)

        if karttype == 'Punkter':
            streamlit_folium.folium_static(create_point_map(filtered_df))
        if karttype == 'Linjer':
            kart(filtered_df)
        #except:
        st.write('Ugylding vegreferanse eller vegreferanse uten skredhendelser')
    
if utvalg == 'Kontraktsområde':
    st.write('Ikkje implementert enda')
