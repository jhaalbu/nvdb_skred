import streamlit as st
import pandas as pd
import nvdbapiv3
import altair as alt
from shapely import wkt
import folium
from folium.plugins import Draw
import streamlit_folium
from streamlit_folium import st_folium
from io import BytesIO
from datetime import datetime
from nvdbskred.kartfunksjoner import kart, create_point_map
from nvdbskred.plotfunksjoner import plot, skred_type_counts, skred_type_by_month, style_function
import requests
from pyproj import Transformer
import json

st.set_page_config(page_title='NVDB skreddata', page_icon=None, layout="centered", initial_sidebar_state="auto", menu_items=None)

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

def feilmelding():
    st.write('Feil oppstått, mest truleg feil vegreferanse. Prøv igjen med ny vegreferanse.')

@st.cache_data
def databehandling(filter):
    skred = nvdbapiv3.nvdbFagdata(445)
    skred.filter(filter)
    #st.write(f'Antall skredregisteringar på strekninga: {skred.statistikk()["antall"]} stk')
    #st.write(f'Total lengde registert for registerte skredhendingar: {int(skred.statistikk()["lengde"])} meter')
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

def last_ned_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data

@st.cache_data
def kontraktsfunksjon():
    r = requests.get('https://nvdbapiles-v3.atlas.vegvesen.no/omrader/kontraktsomrader')
    data = r.json()
    return data

def nedlasting(df):
    return st.download_button(
                "Last ned skredpunkt",
                df.to_csv().encode("utf-8"),
                "skredpunkt.csv",
                "text/csv",
                key="download-csv",
            )

@st.cache_data
def vegref(nord, ost, maks_avstand=50, srid=4326):
    r = requests.get(f"https://nvdbapiles-v3.atlas.vegvesen.no/posisjon?lat={nord}&lon={ost}&maks_avstand={maks_avstand}&maks_antall=1&srid={srid}")
    data = r.json()
    print(json.dumps(data[0], indent=4))
    vegreferanse = {
        'kortform' : data[0]['vegsystemreferanse']['kortform'],
        'vegkategori' : data[0]['vegsystemreferanse']['vegsystem']['vegkategori'],
        'fase' : data[0]['vegsystemreferanse']['vegsystem']['fase'],
        'nummer' : data[0]['vegsystemreferanse']['vegsystem']['nummer'],
        'strekning' : data[0]['vegsystemreferanse']['strekning']['strekning'],
        'delstrekning' : data[0]['vegsystemreferanse']['strekning']['delstrekning'],
        'meter' : data[0]['vegsystemreferanse']['strekning']['meter']
    }
    return vegreferanse

st.title('NVDB skreddata')
st.write('Henter data fra NVDB api v3, ved nedhenting av fylker og heile landet tek det ein del tid å hente data')

transformer = Transformer.from_crs(4326, 5973)



nvdbfilter = {}
referansetype = None
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


referansevalg = st.radio('Velg vegreferanseinput', ['Landsdekkende', 'Kart', 'Vegreferanse'], horizontal=True)

if referansevalg == 'Kart':
    # Setter opp kartobjekt, med midtpunkt og zoom nivå
    st.write('Bruk markør og velg to punkter for å definere strekning (OBS! kunn to markører i kartet)')
    m = folium.Map(location=[62.14497, 9.404296], zoom_start=5)
    #Legger til norgeskart som bakgrunn
    folium.raster_layers.WmsTileLayer(
        url="https://opencache.statkart.no/gatekeeper/gk/gk.open_gmaps?layers=topo4&zoom={z}&x={x}&y={y}",
        name="Norgeskart",
        fmt="image/png",
        layers="topo4",
        attr='<a href="http://www.kartverket.no/">Kartverket</a>',
        transparent=True,
        overlay=True,
        control=True,
    ).add_to(m)
    draw = Draw(
    draw_options={
        'polyline': False,
        'polygon': False,
        'rectangle': False,
        'circle': False,
        'circlemarker': False,
        'marker': True
    }, position='topleft', filename='skredkart.geojson', export=True,
    )
    draw.add_to(m)

    # Litt knotete måte å hente ut koordinater fra Streamlit, kanskje bedre i nye versjoner av streamlit? Ev. litt bedre måte i rein javascript?

    output = st_folium(m, width=700, height=500)
    try:
        pos1 = output["all_drawings"][0]["geometry"]["coordinates"]
        pos2 = output["all_drawings"][1]["geometry"]["coordinates"]
        #st.write(pos1[0])
        #st.write(output["all_drawings"][0]["geometry"]["coordinates"])
        #st.write(output["all_drawings"][1]["geometry"]["coordinates"])

        vegref1 = vegref(pos1[1], pos1[0])
        vegref2 = vegref(pos2[1], pos2[0])
        #st.write(f'Vegref1 : {vegref1}')
        #st.write(f'Vegref2 : {vegref2}')

        if vegref1['strekning'] > vegref2['strekning']:
            vegref1, vegref2 = vegref2, vegref1
        delstrekning_fra = vegref1['strekning']
        delstrekning_til = vegref2['strekning']
        meterverdi_fra = vegref1['meter']
        meterverdi_til = vegref2['meter']

        st.write(f'Fra vegreferanse: {vegref1["kortform"]} til vegreferanse {vegref2["kortform"]}')
        vegreferanse = f'{vegref1["vegkategori"]}{vegref1["fase"]}{vegref1["nummer"]}S{vegref1["strekning"]}-{vegref2["strekning"]}'
        referansetype = 'delstrekning'
        nvdbfilter['vegsystemreferanse'] = vegreferanse
    except (TypeError, IndexError):
        st.error('Sett to markører i kartet, på samme vegnummer.')
    except KeyError:
        st.error('Sjekk om du har valgt punkter på samme vegnummer. Prøv igjen med nye punkter.')
        st.error('Markør må vere innan 30 meter fra veg, ved fleire nære vegar må din veg vere den nærmaste.')
    #st.write(output)

if referansevalg == 'Vegreferanse':
    vegnummer = st.text_input('Vegnummer', 'Rv5')
    col1, col2 = st.columns(2)
    with col1:
        delstrekning_fra = st.number_input('Delstrekning fra (S1D1 = 1)', value=0, min_value=0)
        delstrekning_til = st.number_input('Delstrekning til (S8D1 = 8)', value=0, min_value=0)
    with col2:
        meterverdi_fra = st.number_input('Meterverdi fra', value=0, min_value=0)
        meterverdi_til = st.number_input('Meterverdi til', value=0, min_value=0)

    if delstrekning_fra == 0 and delstrekning_til == 0 and meterverdi_til == 0:
        vegreferanse = vegnummer
        referansetype = 'enkel'
    else:
        vegreferanse = f'{vegnummer}S{delstrekning_fra}-{delstrekning_til}'
        referansetype = 'delstrekning'
    nvdbfilter['vegsystemreferanse'] = vegreferanse

col_1, col_2 = st.columns(2)
with col_1:
    fylkeboks = st.checkbox('Filtrer på fylker')
with col_2:
    kontraktboks = st.checkbox('Filtrer på kontraktområder')
if fylkeboks:
    fylke = st.selectbox(
        'Velg fylke',
        ('Agder', 'Innlandet', 'Møre og Romsdal', 'Nordland',  'Oslo', 'Rogaland', 'Troms og Finnmark', 'Trøndelag',  'Vestfold og Telemark', 'Vestland', 'Viken'))
    nvdbfilter['fylke'] = fylker[fylke]
else:
    fylke = None
if kontraktboks:
    data = kontraktsfunksjon()
    if not fylke or not fylkeboks:
        kontraktliste = [obj["navn"] for obj in data]
    else:
        fylkefilter = int(fylker[fylke])
        filtrert = [obj for obj in data if fylkefilter in obj["fylker"]]
        kontraktliste = [obj["navn"] for obj in filtrert]
    kontrakt = st.selectbox('Velg kontraktsområde', kontraktliste)
    nvdbfilter['kontraktsomrade'] = kontrakt
    if 'fylke' in nvdbfilter:
        kontraktfylke = st.checkbox('Vis kontraktområde ut over fylkesgrenser (overstyrer fylkevalg)')
        if kontraktfylke:
            nvdbfilter.pop('fylke')

st.divider()

vis_kart = st.checkbox('Vis kart')
if vis_kart:
    karttype = st.radio('Vis kart med linjer eller punkter', ['Linjer', 'Punkter'])
    st.write('OBS! Punkter gir senterpunkt av linjene') 
#st.write(nvdbfilter)  
vis_data = st.button('Hent skreddata')

if vis_data:
    try:
        df_data = databehandling(nvdbfilter)
        df_utvalg = filter_df(df_data, losneomrade, fradato, tildato)
        
        if referansetype == 'delstrekning':
            #st.write('delstrekning')
            #st.write(f'delstrekning fra {delstrekning_fra} til {delstrekning_til}')
            #st.write(f'meterverdi fra {meterverdi_fra} til {meterverdi_til}')
            # Extract segment as int
            df_utvalg['segment'] = df_utvalg['vref'].str.extract(r'S(\d+)D\d+').astype(int)
            df_utvalg[['start_distance', 'end_distance']] = df_utvalg['vref'].str.extract(r'm(\d+)-(\d+)')

            # Convert the extracted distances to int
            df_utvalg['start_distance'] = df_utvalg['start_distance'].astype(int)
            df_utvalg['end_distance'] = df_utvalg['end_distance'].astype(int)

            #Filtrerer ut for å få delstrekning basert på meterverdier
            # condition1 = (df_utvalg['segment'] == int(delstrekning_fra)) & (df_utvalg['start_distance'] >= int(meterverdi_fra))
            # condition2 = (df_utvalg['segment'] >= int(delstrekning_fra)) & (df_utvalg['segment'] <= int(delstrekning_til))
            # condition3 = (df_utvalg['segment'] == int(delstrekning_til)) & (df_utvalg['end_distance'] <= int(meterverdi_til))
            # condition1_df = df_utvalg[condition1]
            # st.write(condition1_df)

            # condition2_df = df_utvalg[condition2]
            # st.write(condition2_df)

            # condition3_df = df_utvalg[condition3]
            # st.write(condition3_df)
            # filtered_df = df_utvalg[condition1 | condition2 | condition3]


            condition1 = (df_utvalg['segment'] == int(delstrekning_fra)) & (df_utvalg['start_distance'] >= int(meterverdi_fra))

            # Rows where 'segment' is greater than 'delstrekning_fra' and less than 'delstrekning_til'
            condition2 = (df_utvalg['segment'] > int(delstrekning_fra)) & (df_utvalg['segment'] < int(delstrekning_til))

            # Rows where 'segment' is equal to 'delstrekning_til' and 'end_distance' is less than or equal to 'meterverdi_til'
            condition3 = (df_utvalg['segment'] == int(delstrekning_til)) & (df_utvalg['end_distance'] <= int(meterverdi_til))

            

            # Combine the conditions
            filtered_df = df_utvalg[condition1 | condition2 | condition3]
            #st.write(df_utvalg['segment'])
            #st.write(df_utvalg)
            #st.write(filtered_df)

        elif referansetype == 'enkel':
            filtered_df = df_utvalg
        else:
            filtered_df = df_utvalg
        nedlasting(filtered_df)

        st.altair_chart(plot(filtered_df), use_container_width=True)
        st.altair_chart(skred_type_counts(filtered_df), use_container_width=True)
        st.altair_chart(skred_type_by_month(filtered_df), use_container_width=True)

        if vis_kart:
            if karttype == 'Punkter':
                streamlit_folium.folium_static(create_point_map(filtered_df))
            if karttype == 'Linjer':
                kart(filtered_df)
    except KeyError:
        st.error('Feilmelding! Sjekk om det er motsetningar i filterkriterier, f.eks vegreferanse utanfor fylke, eller kontraktsområde.')

    
st.divider()
st.divider()

# karttype = None
# col_uttak, col_kart = st.columns(2)
# with col_uttak:
#     utvalg = st.radio('Velg utaksmåte', ['Veg', 'Vegreferanse', 'Landsdekkande', 'Fylke', 'Kontraktsområde', 'Filter'])
# with col_kart:
#     vis_kart = st.checkbox('Vis kart')
#     if vis_kart:
#         karttype = st.radio('Vis kart med linjer eller punkter', ['Linjer', 'Punkter'])
#         st.write('OBS! Punkter gir senterpunkt av linjene')
# st.divider()


# if utvalg == 'Fylke':
#     st.write('OBS! Kan ta lang tid å hente data')
#     fylke = st.selectbox(
#     'Velg fylke',
#     ('Agder', 'Innlandet', 'Møre og Romsdal', 'Nordland',  'Oslo', 'Rogaland', 'Troms og Finnmark', 'Trøndelag',  'Vestfold og Telemark', 'Vestland', 'Viken'))
#     #vegtype = st.multiselect(
#     #'Velg vegtype',
#     #['Ev', 'Rv', 'Fv'],
#     #['Ev', 'Rv', 'Fv'])

#     vegreferanse = st.text_input('Videre filtrering på vegreferanse, f.eks Fv, Ev, Rv, eller spesifikk veg som Rv13, eller delstrekning som Rv5 S8D1', '')


#     if st.button('Hent skreddata'):
#         try:
#             if vegreferanse == '':
#                 filter = {'fylke': fylker[fylke]}
#             else:   
#                 filter = {'fylke': fylker[fylke], 'vegsystemreferanse': vegreferanse}
#             df_data = databehandling(filter)
#             df = filter_df(df_data, losneomrade, fradato, tildato)

#             st.altair_chart(plot(df), use_container_width=True)
#             st.altair_chart(skred_type_counts(df), use_container_width=True)
#             st.altair_chart(skred_type_by_month(df), use_container_width=True)
#             if karttype == 'Punkter':
#                 streamlit_folium.folium_static(create_point_map(df))
#             if karttype == 'Linjer':
#                 kart(df)
#         except ValueError:
#             st.write('Feil oppstått, mest truleg feil vegreferanse. Prøv igjen med ny vegreferanse.')
#         except KeyError:
#             st.write('Ingen skredpunkt funnet på strekninga, eller ingen gyldig strekning.')

# if utvalg == 'Landsdekkande':
#     st.write('OBS! Tar lang tid å hente data')

#     if st.button('Hent skreddata'):
#         try:
#             filter = {}
#             df_data = databehandling(filter)
#             df_utvalg = filter_df(df_data, losneomrade, fradato, tildato)
#             st.download_button(
#                 "Last ned skredpunkt",
#                 df_utvalg.to_csv().encode("utf-8"),
#                 "skredpunkt.csv",
#                 "text/csv",
#                 key="download-csv",
#             )
#             st.altair_chart(plot(df_utvalg), use_container_width=True)
#             st.altair_chart(skred_type_counts(df_utvalg), use_container_width=True)
#             st.altair_chart(skred_type_by_month(df_utvalg), use_container_width=True)
#             if karttype == 'Punkter':
#                 streamlit_folium.folium_static(create_point_map(df_utvalg))
#             if karttype == 'Linjer':
#                 kart(df_utvalg)
#         except ValueError:
#             st.write('Feil med API kall, prøv igjen senere')

# if utvalg == 'Veg':
 
#     st.write('Eksempel: Rv5, Fv53, Ev39')
#     st.write('Det går og an å gi inn Rv, Ev, eller Fv for alle skred på vegklassene.')
#     vegreferanse = st.text_input('Vegreferanse', 'Rv5')

#     if st.button('Hent skreddata'):
#         try:
#             filter = {'vegsystemreferanse' : vegreferanse}
#             df_data = databehandling(filter)
#             df_utvalg = filter_df(df_data, losneomrade, fradato, tildato)
#             st.download_button(
#                 "Last ned skredpunkt",
#                 df_utvalg.to_csv().encode("utf-8"),
#                 "skredpunkt.csv",
#                 "text/csv",
#                 key="download-csv",
#             )
#             st.altair_chart(plot(df_utvalg), use_container_width=True)
#             st.altair_chart(skred_type_counts(df_utvalg), use_container_width=True)
#             st.altair_chart(skred_type_by_month(df_utvalg), use_container_width=True)

#             if karttype == 'Punkter':
#                 streamlit_folium.folium_static(create_point_map(df_utvalg))
#             if karttype == 'Linjer':
#                 kart(df_utvalg)
#         except ValueError:
#             feilmelding()


# if utvalg == 'Vegreferanse':
#     # pos1 = output["all_drawings"][0]["geometry"]["coordinates"]
#     # pos2 = output["all_drawings"][1]["geometry"]["coordinates"]
#     # st.write(pos1[0])
#     # st.write(output["all_drawings"][0]["geometry"]["coordinates"])
#     # st.write(output["all_drawings"][1]["geometry"]["coordinates"])
#     # st.write(vegreferanse(pos1[1], pos1[0]))
#     # st.write(vegreferanse(pos2[1], pos2[0]))
#     #st.write(output)
#     st.write('Her går det an å gi inn vegreferanse for å hente ut skredpunkt for delstrekning, og meterverdi.')
#     vegnummer = st.text_input('Vegnummer', 'Rv5')
#     col1, col2 = st.columns(2)
#     with col1:
#         delstrekning_fra = st.number_input('Delstrekning fra (S1D1 = 1)', value=0, min_value=0)
#         delstrekning_til = st.number_input('Delstrekning til (S8D1 = 8)', value=0, min_value=0)
#     with col2:
#         meterverdi_fra = st.number_input('Meterverdi fra', value=0, min_value=0)
#         meterverdi_til = st.number_input('Meterverdi til', value=0, min_value=0)
    
#     if delstrekning_fra == 0 and delstrekning_til == 0 and meterverdi_til == 0:
#         vegreferanse = vegnummer
#         referansetype = 'enkel'
#     else:
#         vegreferanse = f'{vegnummer}S{delstrekning_fra}-{delstrekning_til}'
#         referansetype = 'delstrekning'
    

#     if st.button('Hent skreddata'):
#         st.write(vegreferanse)
#         try:
#             filter = {'vegsystemreferanse' : vegreferanse}
#             df_data = databehandling(filter)
#             df_utvalg = filter_df(df_data, losneomrade, fradato, tildato)
            
#             if referansetype == 'delstrekning':
            
#                 # Extract segment as int
#                 df_utvalg['segment'] = df_utvalg['vref'].str.extract(r'S(\d+)D\d+').astype(int)
#                 df_utvalg[['start_distance', 'end_distance']] = df_utvalg['vref'].str.extract(r'm(\d+)-(\d+)')

#                 # Convert the extracted distances to int
#                 df_utvalg['start_distance'] = df_utvalg['start_distance'].astype(int)
#                 df_utvalg['end_distance'] = df_utvalg['end_distance'].astype(int)

#                 #Filtrerer ut for å få delstrekning basert på meterverdier
#                 condition1 = (df_utvalg['segment'] == delstrekning_fra) & (df_utvalg['start_distance'] >= meterverdi_fra)
#                 condition2 = (df_utvalg['segment'] > delstrekning_fra) & (df_utvalg['segment'] < delstrekning_til)
#                 condition3 = (df_utvalg['segment'] == delstrekning_til) & (df_utvalg['end_distance'] <= meterverdi_til)

#                 filtered_df = df_utvalg[condition1 | condition2 | condition3]
#                 #st.write(filtered_df)

#             if referansetype == 'enkel':
#                 filtered_df = df_utvalg

#             nedlasting(filtered_df)

#             st.altair_chart(plot(filtered_df), use_container_width=True)
#             st.altair_chart(skred_type_counts(filtered_df), use_container_width=True)
#             st.altair_chart(skred_type_by_month(filtered_df), use_container_width=True)

#             if karttype == 'Punkter':
#                 streamlit_folium.folium_static(create_point_map(filtered_df))
#             if karttype == 'Linjer':
#                 kart(filtered_df)
#         except ValueError:
#             feilmelding()
#         except KeyError:
#             st.write('Ingen skredpunkt funnet på strekninga, eller ingen gyldig strekning.')
    
# if utvalg == 'Kontraktsområde':
#     r = requests.get('https://nvdbapiles-v3.atlas.vegvesen.no/omrader/kontraktsomrader')
#     data = r.json()
#     fylke = st.selectbox(
#         'Velg fylke',
#         ('Alle', 'Agder', 'Innlandet', 'Møre og Romsdal', 'Nordland',  'Oslo', 'Rogaland', 'Troms og Finnmark', 'Trøndelag',  'Vestfold og Telemark', 'Vestland', 'Viken'))
#     if fylke == 'Alle':
#         kontraktliste = [obj["navn"] for obj in data]
#     else:
#         fylkefilter = int(fylker[fylke])
#         filtrert = [obj for obj in data if fylkefilter in obj["fylker"]]
#         kontraktliste = [obj["navn"] for obj in filtrert]
#     kontrakt = st.selectbox('Velg kontraktsområde', kontraktliste)
#     if st.button('Hent skreddata'):
#         filter = {'kontraktsomrade' : kontrakt}
#         df_data = databehandling(filter)
#         df_utvalg = filter_df(df_data, losneomrade, fradato, tildato)
#         st.altair_chart(plot(df_utvalg), use_container_width=True)
#         st.altair_chart(skred_type_counts(df_utvalg), use_container_width=True)
#         st.altair_chart(skred_type_by_month(df_utvalg), use_container_width=True)
#         if karttype == 'Punkter':
#             streamlit_folium.folium_static(create_point_map(df_utvalg))
#         if karttype == 'Linjer':
#             kart(df_utvalg)



    
# st.write('For spørsmål eller tilbakemelding kontakt: jan.helge.aalbu@vegvesen.no')
