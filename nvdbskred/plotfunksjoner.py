import altair as alt
import streamlit as st
import pandas as pd
from io import BytesIO
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
    data_df['month'] = data_df.loc[:,'Skred_dato'].dt.strftime('%B')
    
    # Translate month names to Norwegian
    data_df.loc[:, 'month'] = data_df.loc[:,'month'].map(month_mapping)

    # Group data by month and type and count occurrences
    data_grouped = data_df.groupby(['month', 'Type_skred']).size().reset_index(name='count')

    # Color mapping
    #

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
