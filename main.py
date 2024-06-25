import json

import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely.geometry import Polygon, shape
from streamlit_option_menu import option_menu

from graficos import (
    generar_grafico1,
    generar_grafico2,
    generar_grafico3,
    generar_grafico4,
    generar_grafico5,
)

file_path = "quejas-final.parquet"
vul_file_path = "vulnerabilidad-por-barrios.csv"
contactos = {
    "Ainhoa Prado": "apraalo@upv.edu.es",
    "Lucia Fuentes": "lfuerub@etsinf.upv.es",
    "Antonio Moraga": "agarmor4@etsinf.upv.es",
}


# Función para simplificar geometrías
def convert_and_simplify(geojson_str, tolerance=0.001):
    geom = shape(json.loads(geojson_str))
    if isinstance(geom, Polygon):
        return geom.simplify(tolerance)
    else:
        return geom


# Lee el archivo Parquet
df = pd.read_parquet(
    file_path,
    columns=["barrio_localización", "tipo_solicitud", "geo_shape", "fecha_entrada_ayuntamiento"],
)
df["fecha_entrada_ayuntamiento"] = pd.to_datetime(df["fecha_entrada_ayuntamiento"])
df["geometry"] = df["geo_shape"].apply(lambda x: convert_and_simplify(x))
gdf = gpd.GeoDataFrame(df, geometry="geometry")

# Lee el archivo CSV
dfvul = pd.read_csv(vul_file_path, sep=";")

conteo_barrio_tipo = (
    df.groupby(
        [
            "barrio_localización",
            "tipo_solicitud",
            df["fecha_entrada_ayuntamiento"].dt.to_period("M"),
        ]
    )
    .size()
    .reset_index(name="count")
)


# Función para convertir DataFrame a CSV
@st.cache_data
def convert_df(df):
    # Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


# Configurar el menú lateral
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=[
            "Contact",
            "Acquisition of datasets",
            "Number of complaints by type",
            "Type of applications mapping",
            "Evolution of applications over time",
            "Dynamic evolution on map",
            "Vulnerability and applications",
        ],
        icons=[
            "envelope",
            "database",
            "bar-chart",
            "bar-chart",
            "bar-chart",
            "bar-chart",
            "bar-chart",
        ],
        menu_icon="cast",
        default_index=0,
    )

if selected == "Contact":
    st.subheader("Contact")
    for nombre, email in contactos.items():
        st.write(f"{nombre}: {email}")

    # Contact Form
    with st.expander("Contact us"):
        with st.form(key="contact", clear_on_submit=True):
            email = st.text_input("Contact Email")
            st.text_area(
                "Query",
                "Please fill in all the information or we may not be able to process your request",
            )
            submit_button = st.form_submit_button(label="Send Information")
            if submit_button:
                st.success("Your query has been sent successfully!")

if selected == "Acquisition of datasets":
    st.subheader("Acquisition of datasets")
    st.write("Here you can download the datasets used in this analysis.")

    st.write("### Download quejas-final dataset")
    csv_final = convert_df(df)
    st.download_button(
        label="Download quejas-final as CSV",
        data=csv_final,
        file_name="quejas-final.csv",
        mime="text/csv",
    )

    st.write("### Download vulnerabilidad-por-barrios dataset")
    csv_vul = convert_df(dfvul)
    st.download_button(
        label="Download vulnerabilidad-por-barrios as CSV",
        data=csv_vul,
        file_name="vulnerabilidad-por-barrios.csv",
        mime="text/csv",
    )

if selected == "Number of complaints by type":
    st.subheader("Number of complaints by type")
    c1, c2 = st.columns(2)
    fig = generar_grafico1(file_path=file_path)

    with c1:
        # st.write("Gráfico 2A")
        # Aquí puedes insertar el código para generar tu gráfico
        # st.write("Insertar gráfico aquí")
        st.plotly_chart(figure_or_data=fig[0], use_container_width=True)

    with c2:
        # st.write("Gráfico 2B")
        # Aquí puedes insertar el código para generar tu gráfico
        # st.write("Insertar gráfico aquí")
        st.plotly_chart(figure_or_data=fig[1], use_container_width=True)


if selected == "Type of applications mapping":
    st.subheader("Type of applications mapping")
    c1, c2 = st.columns(2)
    fig = generar_grafico2(file_path=file_path)

    with c1:
        st.plotly_chart(figure_or_data=fig[0], use_container_width=True)

    with c2:
        st.plotly_chart(figure_or_data=fig[1], use_container_width=True)

if selected == "Evolution of applications over time":
    st.subheader("Evolution of applications over time")
    fig = generar_grafico3(file_path=file_path)
    st.pyplot(fig)

if selected == "Dynamic evolution on map":
    st.subheader("Dynamic evolution on map")
    fig = generar_grafico4()
    st.plotly_chart(fig)

if selected == "Vulnerability and applications":
    st.subheader("Vulnerability and applications")
    c1, c2 = st.columns(2)
    fig = generar_grafico5()

    with c1:
        st.plotly_chart(figure_or_data=fig[0], use_container_width=True)

    with c2:
        st.plotly_chart(figure_or_data=fig[1], use_container_width=True)
# Run the app using `streamlit run your_script_name.py`
