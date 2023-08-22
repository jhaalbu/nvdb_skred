import streamlit as st
import pandas as pd
import nvdbapiv3

st.title('NVDB skreddata')

vegreferanse = st.text_input('Vegreferanse', 'Rv5 S8D1')

skred = nvdbapiv3.nvdbFagdata(445)
skred.filter({'vegsystemreferanse' : vegreferanse})

df = pd.DataFrame.from_records(skred.to_records())
df_utvalg = df[['Skred dato', 'Type skred', 'Volum av skredmasser på veg', 'Stedsangivelse', 'Værforhold på vegen', 'Blokkert veglengde', 'geometri', 'vref']]

df_utvalg.columns = df_utvalg.columns.str.replace(' ', '_')
df_utvalg['Skred_dato'] = df['Skred dato'].astype('datetime64[ns]')

st.write(df_utvalg)


data = df_utvalg.pivot_table(
    index=df_utvalg.Skred_dato.dt.year,
    columns='Type_skred',
    aggfunc='size')

st.bar_chart(data)