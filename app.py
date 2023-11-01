import streamlit as st
import pandas as pd
import nvdbapiv3
import altair as alt
import geopandas as gpd
from shapely import wkt
import folium
import streamlit_folium
from io import BytesIO
from datetime import datetime
from datetime import datetime

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
    #folium.TileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', 
    #             name="CartoDB Dark Matter", 
    #             attr="© OpenStreetMap contributors, © CartoDB").add_to(m)
    for _, row in gdf_wgs84.iterrows():
        geojson_row = gpd.GeoDataFrame([row]).to_json()
        folium.GeoJson(
            geojson_row,
            style_function=style_function
        ).add_to(m)
    return streamlit_folium.folium_static(m)

def last_ned_shape(df, type='linje'):
    st.write(df)
    df['Skred_dato'] = df['Skred_dato'].astype(str)
    df['geometri'] = df['geometri'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry='geometri')
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

@st.cache_data
def databehandling(filter):
    skred = nvdbapiv3.nvdbFagdata(445)
    skred.filter(filter)
    st.write(f'Antall skredregisteringar på strekninga: {skred.statistikk()["antall"]} stk')
    st.write(f'Total lengde registert for registerte skredhendingar: {int(skred.statistikk()["lengde"])} meter')
    df = pd.DataFrame.from_records(skred.to_records())
    df_utvalg = df[['Skred dato', 'Type skred', 'Volum av skredmasser på veg', 
                    'Stedsangivelse', 'Løsneområde', 'Værforhold på vegen', 'Blokkert veglengde', 
                    'geometri', 'vref']].copy() 
    df_utvalg.columns = df_utvalg.columns.str.replace(' ', '_')
    df_utvalg['Skred_dato'] = pd.to_datetime(df_utvalg['Skred_dato'], errors='coerce')
    return df_utvalg

def filter_df(df, losneomrade, fradato, tildato):
    filtered_df = df[(df['Skred_dato'] >= fradato) & 
                 (df['Skred_dato'] <= tildato) & 
                 (df['Løsneområde'].isin(losneomrade))]
    return filtered_df

def filter_df(df, losneomrade, fradato, tildato):
    filtered_df = df[(df['Skred_dato'] >= fradato) & 
                 (df['Skred_dato'] <= tildato) & 
                 (df['Løsneområde'].isin(losneomrade))]
    return filtered_df

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
col_tid_fra, col_tid_til = st.columns(2)
with col_tid_fra:
    fradato = st.date_input('Fra dato', value=pd.to_datetime('2000-01-01'), min_value=pd.to_datetime('1900-01-01'), max_value=pd.to_datetime(datetime.today().strftime('%Y-%m-%d')))
    fradato = str(fradato)
with col_tid_til:
    tildato = st.date_input('Til dato', value=pd.to_datetime(datetime.today().strftime('%Y-%m-%d')), min_value=pd.to_datetime('1900-01-01'), max_value=pd.to_datetime(datetime.today().strftime('%Y-%m-%d')))
    tildato = str(tildato)
losneomrade = st.multiselect(
    'Velg løsneområder',
    ['Fjell/dalside', 'Vegskjæring', 'Ur', 'Inne i tunnel', 'Tunnelmunning (historisk)'],
    ['Fjell/dalside', 'Vegskjæring'])

col_uttak, col_kart = st.columns(2)
with col_uttak:
    utvalg = st.radio('Velg utaksmåte', ['Veg', 'Vegreferanse', 'Landsdekkande', 'Fylke', 'Kontraktsområde'])
with col_kart:
    vis_kart = st.checkbox('Vis kart')
    if vis_kart:
        karttype = st.radio('Vis kart med linjer eller punkter', ['Linjer', 'Punkter'])
        st.write('OBS! Punkter gir senterpunkt av linjene')
st.divider()


if utvalg == 'Fylke':
    st.write('OBS! Kan ta lang tid å hente data')
    fylke = st.selectbox(
    'Velg fylke',
    ('Agder', 'Innlandet', 'Møre og Romsdal', 'Nordland',  'Oslo', 'Rogaland', 'Troms og Finnmark', 'Trøndelag',  'Vestfold og Telemark', 'Vestland', 'Viken'))
    
    vegreferanse = st.text_input('Videre eventuell filtrering på vegreferanse, f.eks Fv, Ev, Rv, Rv13, eller delstrekning som Rv5 S8D1', '')
    
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
        try:   
            if vegreferanse == '':
                filter = {'fylke': fylker[fylke]}
            else:   
                filter = {'fylke': fylker[fylke], 'vegsystemreferanse': vegreferanse}
            df_data = databehandling(filter)
            df = filter_df(df_data, losneomrade, fradato, tildato)
            st.download_button(
                "Last ned skredpunkt",
                df.to_csv().encode("utf-8"),
                "klimadata.csv",
                "text/csv",
                key="download-csv",
            )
            st.altair_chart(plot(df), use_container_width=True)
            st.altair_chart(skred_type_counts(df), use_container_width=True)
            st.altair_chart(skred_type_by_month(df), use_container_width=True)
            if karttype == 'Punkter':
                streamlit_folium.folium_static(create_point_map(df))
            if karttype == 'Linjer':
                kart(df)
        except ValueError:
            st.write('Feil oppstått, mest truleg feil vegreferanse. Prøv igjen med ny vegreferanse.')
        except KeyError:
            st.write('Ingen skredpunkt funnet på strekninga, eller ingen gyldig strekning.')

if utvalg == 'Landsdekkande':
    st.write('OBS! Tar lang tid å hente data')

    if st.button('Hent skreddata'):
        try:
            filter = {}
            df_data = databehandling(filter)
            df_utvalg = filter_df(df_data, losneomrade, fradato, tildato)
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
            if karttype == 'Punkter':
                streamlit_folium.folium_static(create_point_map(df_utvalg))
            if karttype == 'Linjer':
                kart(df_utvalg)
        except ValueError:
            st.write('Feil oppstått, mest truleg feil vegreferanse. Prøv igjen med ny vegreferanse.')
        except KeyError:
            st.write('Ingen skredpunkt funnet på strekninga, eller ingen gyldig strekning.')

if utvalg == 'Veg':
 
    st.write('Eksempel: Rv5, Fv53, Ev39')
    st.write('Det går og an å gi inn Rv, Ev, eller Fv for alle skred på vegklassene.')
    vegreferanse = st.text_input('Vegreferanse', 'Rv5')

    if st.button('Hent skreddata'):
        try:
            filter = {'vegsystemreferanse' : vegreferanse}
            df_data = databehandling(filter)
            df_utvalg = filter_df(df_data, losneomrade, fradato, tildato)
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

            if karttype == 'Punkter':
                streamlit_folium.folium_static(create_point_map(df_utvalg))
            if karttype == 'Linjer':
                kart(df_utvalg)
        except ValueError:
            st.write('Feil oppstått, mest truleg feil vegreferanse. Prøv igjen med ny vegreferanse.')
        except KeyError:
            st.write('Ingen skredpunkt funnet på strekninga, eller ingen gyldig strekning.')


if utvalg == 'Vegreferanse':
    st.write('Her går det an å gi inn vegreferanse for å hente ut skredpunkt for delstrekning, og meterverdi.')
    vegnummer = st.text_input('Vegnummer', 'Rv5')
    col1, col2 = st.columns(2)
    with col1:
        delstrekning_fra = st.number_input('Delstrekning fra (S1D1 = 1)', value=11, min_value=1)
        delstrekning_til = st.number_input('Delstrekning til (S8D1 = 8)', value=8, min_value=1)
    with col2:
        meterverdi_fra = st.number_input('Meterverdi fra', value=0)
        meterverdi_til = st.number_input('Meterverdi til', value=20000, min_value=0)
    vegreferanse = f'{vegnummer}S{delstrekning_fra}-{delstrekning_til}'

    

    if st.button('Hent skreddata'):
        try:
            filter = {'vegsystemreferanse' : vegreferanse}
            df_data = databehandling(filter)
            df_utvalg = filter_df(df_data, losneomrade, fradato, tildato)
            
            
            # Extract segment as int
            df_utvalg['segment'] = df_utvalg['vref'].str.extract(r'S(\d+)D\d+').astype(int)
            df_utvalg[['start_distance', 'end_distance']] = df_utvalg['vref'].str.extract(r'm(\d+)-(\d+)')

            # Convert the extracted distances to int
            df_utvalg['start_distance'] = df_utvalg['start_distance'].astype(int)
            df_utvalg['end_distance'] = df_utvalg['end_distance'].astype(int)

            #Filtrerer ut for å få delstrekning basert på meterverdier
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
        except ValueError:
            st.write('Feil oppstått, mest truleg feil vegreferanse. Prøv igjen med ny vegreferanse.')
        except KeyError:
            st.write('Ingen skredpunkt funnet på strekninga, eller ingen gyldig strekning.')

    
if utvalg == 'Kontraktsområde':
    st.write('Ikkje implementert enda')

st.write('For spørsmål eller tilbakemelding kontakt: jan.helge.aalbu@vegvesen.no')
