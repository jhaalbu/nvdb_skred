import folium
import streamlit_folium
import geopandas as gpd
from nvdbskred.plotfunksjoner import style_function
from shapely import wkt
import pandas as pd

def kart(df):
    df['geometry'] = df.loc[:,'geometri'].apply(wkt.loads)
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

def create_point_map(df):
    # Convert 'geometri' column to GeoSeries
    df['geometry'] = df.loc[:,'geometri'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    # Set the coordinate system for the GeoDataFrame to UTM 33N
    gdf.crs = "EPSG:32633"

    # Compute midpoints
    
 
    # Transform to WGS 84
    gdf = gdf.to_crs("EPSG:4326")

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