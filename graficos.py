import json

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from shapely.geometry import Polygon, shape


def generar_grafico3(file_path):
    # Leer los datos desde el archivo .parquet
    final = pd.read_parquet(file_path)

    # Convertir la columna de fechas a datetime
    final["fecha_entrada_ayuntamiento"] = pd.to_datetime(final["fecha_entrada_ayuntamiento"])

    # Obtener la lista de tipos de solicitud únicos
    tipo_solicitud_unique = final["tipo_solicitud"].unique()

    # Widget de selección múltiple para tipos de solicitud
    selected_tipos = st.multiselect(
        "Selecciona tipos de solicitud",
        options=tipo_solicitud_unique,
        default=tipo_solicitud_unique,
    )

    # Filtrar los datos según las selecciones realizadas
    if selected_tipos:
        final_filtered = final[final["tipo_solicitud"].isin(selected_tipos)]
    else:
        final_filtered = final.copy()

    # Agrupar por fecha y tipo de solicitud
    df_grouped = (
        final_filtered.groupby(
            [final_filtered["fecha_entrada_ayuntamiento"].dt.to_period("D"), "tipo_solicitud"]
        )
        .size()
        .unstack(fill_value=0)
    )

    # Crear el gráfico de áreas apiladas
    fig, ax = plt.subplots(figsize=(12, 8))
    df_grouped.plot(kind="area", colormap="viridis", alpha=0.6, ax=ax)

    # Añadir etiquetas y título
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Número de solicitudes")
    ax.set_title("Evolución de las solicitudes con el tiempo")
    ax.legend(title="Tipo de solicitud")
    ax.grid(True)

    # Ajustar el diseño
    plt.tight_layout()

    # Devolver el objeto de figura (fig) para mostrar en Streamlit
    return fig


def generar_grafico1(file_path):

    # Leer los datos desde el archivo .parquet
    file_path = "quejas-final.parquet"  # Reemplaza con la ruta correcta a tu archivo
    df = pd.read_parquet(file_path)

    # Agrupar por distrito y contar el número de solicitudes
    conteo_distrito = df["distrito_localización"].value_counts().reset_index()
    conteo_distrito.columns = ["distrito_localización", "count"]

    # Calcular la densidad de solicitudes por área (esto requiere tener un campo 'Shape_Area' en tu dataset)
    conteo_distrito = conteo_distrito.merge(
        df[["distrito_localización", "Shape_Area"]].drop_duplicates(), on="distrito_localización"
    )
    conteo_distrito["density"] = conteo_distrito["count"] / conteo_distrito["Shape_Area"]

    # Crear los gráficos de barras
    fig_barras = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=["District Application Count by Type"],
    )

    tipo_solicitud_unique = df["tipo_solicitud"].unique()
    for var in tipo_solicitud_unique:
        conteo_tipo = (
            df[df["tipo_solicitud"] == var]["distrito_localización"].value_counts().reset_index()
        )
        conteo_tipo.columns = ["distrito_localización", "count"]

        fig_barras.add_trace(
            go.Bar(
                x=conteo_tipo["count"],
                y=conteo_tipo["distrito_localización"],
                orientation="h",
                name=var,
            ),
            row=1,
            col=1,
        )

    fig_barras.update_layout(
        title_text="District Application Count by Type", barmode="stack", showlegend=True
    )

    # Leer los datos desde el archivo .parquet
    file_path = "quejas-final.parquet"  # Reemplaza con la ruta correcta a tu archivo
    df = pd.read_parquet(file_path)

    # Agrupar por distrito y contar el número de solicitudes
    conteo_distrito = df["barrio_localización"].value_counts().reset_index()
    conteo_distrito.columns = ["barrio_localización", "count"]

    # Calcular la densidad de solicitudes por área (esto requiere tener un campo 'Shape_Area' en tu dataset)
    conteo_distrito = conteo_distrito.merge(
        df[["barrio_localización", "Shape_Area"]].drop_duplicates(), on="barrio_localización"
    )
    conteo_distrito["density"] = conteo_distrito["count"] / conteo_distrito["Shape_Area"]

    # Crear los gráficos de barras
    fig_barras2 = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=["Neighbourhood Application Count by Type"],
    )

    tipo_solicitud_unique = df["tipo_solicitud"].unique()
    for var in tipo_solicitud_unique:
        conteo_tipo = (
            df[df["tipo_solicitud"] == var]["barrio_localización"].value_counts().reset_index()
        )
        conteo_tipo.columns = ["barrio_localización", "count"]

        fig_barras2.add_trace(
            go.Bar(
                x=conteo_tipo["count"],
                y=conteo_tipo["barrio_localización"],
                orientation="h",
                name=var,
            ),
            row=1,
            col=1,
        )

    fig_barras2.update_layout(
        title_text="Neighbourhood Application Count by Type", barmode="stack", showlegend=True
    )

    return [fig_barras, fig_barras2]


def generar_grafico2(file_path):
    # Leer los datos desde el archivo .parquet
    df = pd.read_parquet(file_path)

    # Filtrar filas con valores None en la columna 'geo_shape' para barrios
    df_barrios = df[df["geo_shape"].notna()]

    # Filtrar filas con valores None en la columna 'geo_shape_dis' para distritos
    df_distritos = df[df["geo_shape_dis"].notna()]

    def convert_and_simplify(geojson_str, tolerance=0.001):
        geom = shape(json.loads(geojson_str))
        if isinstance(geom, Polygon):
            return geom.simplify(tolerance)
        else:
            return geom

    # Convertir las geometrías de 'geo_shape' y 'geo_shape_dis' al formato adecuado para barrios y distritos
    df_barrios["geometry"] = df_barrios["geo_shape"].apply(lambda x: convert_and_simplify(x))
    df_distritos["geometry"] = df_distritos["geo_shape_dis"].apply(
        lambda x: convert_and_simplify(x)
    )

    # Crear GeoDataFrames con las geometrías
    gdf_barrios = gpd.GeoDataFrame(df_barrios, geometry="geometry")
    gdf_distritos = gpd.GeoDataFrame(df_distritos, geometry="geometry")

    # Agrupar por barrio y contar el número de solicitudes
    conteo_barrio = df_barrios["barrio_localización"].value_counts().reset_index()
    conteo_barrio.columns = ["barrio_localización", "count"]

    # Calcular la densidad de solicitudes por área para barrios
    conteo_barrio = conteo_barrio.merge(
        df_barrios[["barrio_localización", "Shape_Area"]].drop_duplicates(),
        on="barrio_localización",
    )
    conteo_barrio["density"] = conteo_barrio["count"] / conteo_barrio["Shape_Area"]

    # Agrupar por distrito y contar el número de solicitudes para distritos
    conteo_distrito = df_distritos["distrito_localización"].value_counts().reset_index()
    conteo_distrito.columns = ["distrito_localización", "count"]

    # Calcular la densidad de solicitudes por área para distritos
    conteo_distrito = conteo_distrito.merge(
        df_distritos[["distrito_localización", "Shape_Area"]].drop_duplicates(),
        on="distrito_localización",
    )
    conteo_distrito["density"] = conteo_distrito["count"] / conteo_distrito["Shape_Area"]

    # Crear figuras para ambos gráficos
    fig_barrios = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=["Application Density per Neighbourhood"],
        specs=[[{"type": "mapbox"}]],
    )

    fig_distritos = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=["Application Density per District"],
        specs=[[{"type": "mapbox"}]],
    )

    # Añadir trazos para barrios
    density_trace_barrios = go.Choroplethmapbox(
        geojson=gdf_barrios.set_index("barrio_localización")["geometry"].__geo_interface__,
        locations=conteo_barrio["barrio_localización"],
        z=conteo_barrio["density"],
        colorscale="YlGnBu",
        colorbar_title="Densidad",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=True,
    )

    count_trace_barrios = go.Choroplethmapbox(
        geojson=gdf_barrios.set_index("barrio_localización")["geometry"].__geo_interface__,
        locations=conteo_barrio["barrio_localización"],
        z=conteo_barrio["count"],
        colorscale="YlOrRd",
        colorbar_title="Conteo",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=False,
    )

    fig_barrios.add_trace(density_trace_barrios, row=1, col=1)
    fig_barrios.add_trace(count_trace_barrios, row=1, col=1)

    # Añadir trazos para distritos
    density_trace_distritos = go.Choroplethmapbox(
        geojson=gdf_distritos.set_index("distrito_localización")["geometry"].__geo_interface__,
        locations=conteo_distrito["distrito_localización"],
        z=conteo_distrito["density"],
        colorscale="YlGnBu",
        colorbar_title="Densidad",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=True,
    )

    count_trace_distritos = go.Choroplethmapbox(
        geojson=gdf_distritos.set_index("distrito_localización")["geometry"].__geo_interface__,
        locations=conteo_distrito["distrito_localización"],
        z=conteo_distrito["count"],
        colorscale="YlOrRd",
        colorbar_title="Conteo",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=False,
    )

    fig_distritos.add_trace(density_trace_distritos, row=1, col=1)
    fig_distritos.add_trace(count_trace_distritos, row=1, col=1)

    # Configuración del mapa de Valencia para barrios
    fig_barrios.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=11,
        mapbox_center={
            "lat": 39.4699,
            "lon": -0.3763,
        },  # Coordenadas para centrar el mapa en Valencia
        title_text="Application Density per Neighbourhood",
    )

    # Configuración del mapa de Valencia para distritos
    fig_distritos.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=11,
        mapbox_center={
            "lat": 39.4699,
            "lon": -0.3763,
        },  # Coordenadas para centrar el mapa en Valencia
        title_text="Application Density per District",
    )

    # Añadir el menú de selección para barrios
    fig_barrios.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {"args": [{"visible": [True, False]}], "label": "Density", "method": "update"},
                    {"args": [{"visible": [False, True]}], "label": "Count", "method": "update"},
                ],
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0,
                "xanchor": "left",
                "y": 1.2,
                "yanchor": "top",
            }
        ]
    )

    # Añadir el menú de selección para distritos
    fig_distritos.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {"args": [{"visible": [True, False]}], "label": "Density", "method": "update"},
                    {"args": [{"visible": [False, True]}], "label": "Count", "method": "update"},
                ],
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0,
                "xanchor": "left",
                "y": 1.2,
                "yanchor": "top",
            }
        ]
    )

    # Devolver las figuras como una lista
    return [fig_barrios, fig_distritos]


def convert_and_simplify(geojson_str, tolerance=0.001):
    geom = shape(json.loads(geojson_str))
    if isinstance(geom, Polygon):
        return geom.simplify(tolerance)
    else:
        return geom


def generar_grafico4():

    df = pd.read_parquet(
        "quejas-final.parquet",
        columns=[
            "barrio_localización",
            "tipo_solicitud",
            "geo_shape",
            "fecha_entrada_ayuntamiento",
        ],
    )
    df["fecha_entrada_ayuntamiento"] = pd.to_datetime(df["fecha_entrada_ayuntamiento"])
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
    df["geometry"] = df["geo_shape"].apply(lambda x: convert_and_simplify(x))

    gdf = gpd.GeoDataFrame(df, geometry="geometry")
    # Crear una figura con subplots
    fig = go.Figure()
    sizes = {"Sugerencia": 10, "Queja": 20, "Defensor": 30, "Síndic": 40, "Otras": 50}

    # Agrupar por fecha para crear frames
    fechas = conteo_barrio_tipo["fecha_entrada_ayuntamiento"].unique()
    fechas = pd.PeriodIndex(fechas)
    fechas = fechas.sort_values()

    fechas = pd.array(fechas)

    frames = []
    for fecha in fechas:
        df_fecha = conteo_barrio_tipo[conteo_barrio_tipo["fecha_entrada_ayuntamiento"] == fecha]
        lat = gdf.loc[
            gdf["barrio_localización"].isin(df_fecha["barrio_localización"]), "geometry"
        ].centroid.y.values
        # Convertir a lista o serie sin NaNs
        lat = pd.Series(lat).dropna()
        lon = gdf.loc[
            gdf["barrio_localización"].isin(df_fecha["barrio_localización"]), "geometry"
        ].centroid.x.values
        # Convertir a lista o serie sin NaNs
        lon = pd.Series(lon).dropna()

        text = df_fecha["tipo_solicitud"]
        text = df_fecha["tipo_solicitud"] + "<br>" + df_fecha["count"].astype(str)
        frame = go.Frame(
            data=[
                go.Scattermapbox(
                    lat=lat,
                    lon=lon,
                    mode="markers",
                    marker=go.scattermapbox.Marker(
                        size=df_fecha["tipo_solicitud"].apply(lambda x: sizes.get(x, 10)),
                        color=df_fecha["count"],
                        showscale=True,
                    ),
                    text=text,
                    hoverinfo="text",
                )
            ],
            name=str(fecha),
        )
        frames.append(frame)

    df_1fecha = conteo_barrio_tipo[conteo_barrio_tipo["fecha_entrada_ayuntamiento"] == fechas[0]]
    text = df_1fecha["tipo_solicitud"] + "<br>" + df_1fecha["count"].astype(str)
    fig.add_trace(
        go.Scattermapbox(
            lat=gdf["geometry"].centroid.y,
            lon=gdf["geometry"].centroid.x,
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=df_1fecha["tipo_solicitud"].apply(lambda x: sizes.get(x, "black")),
                color=conteo_barrio_tipo[
                    conteo_barrio_tipo["fecha_entrada_ayuntamiento"] == fechas[0]
                ]["count"],
                showscale=True,
            ),
            text=text,
            hoverinfo="text",
        )
    )
    df_1fecha
    # print(df_1fecha['tipo_solicitud'].apply(lambda x: colors.get(x, 'black')))

    # Añadir el primer frame de datos al gráfico
    # Configurar el layout del mapa
    fig.update_layout(
        mapbox=dict(style="carto-positron", zoom=11, center=dict(lat=39.4699, lon=-0.3763)),
        title_text="Evolution of Applications by Neighbourhood",
        height=800,
        updatemenus=[
            {
                "buttons": [
                    {
                        "args": [
                            None,
                            {"frame": {"duration": 1000, "redraw": True}, "fromcurrent": True},
                        ],
                        "label": "Play",
                        "method": "animate",
                    },
                    {
                        "args": [
                            [None],
                            {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"},
                        ],
                        "label": "Pause",
                        "method": "animate",
                    },
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 87},
                "showactive": False,
                "type": "buttons",
                "x": 0.1,
                "xanchor": "right",
                "y": 0,
                "yanchor": "top",
            }
        ],
        sliders=[
            {
                "steps": [
                    {
                        "args": [
                            [str(fecha)],
                            {"frame": {"duration": 1000, "redraw": True}, "mode": "immediate"},
                        ],
                        "label": str(fecha),
                        "method": "animate",
                    }
                    for fecha in fechas
                ],
                "active": 0,
                "transition": {"duration": 1000, "easing": "cubic-in-out"},
                "x": 0.1,
                "xanchor": "left",
                "y": 0,
                "yanchor": "top",
                "pad": {"b": 10, "t": 50},
                "len": 0.9,
            }
        ],
    )
    # Añadir frames al gráfico
    fig.frames = frames
    return fig


def generar_grafico5():

    # Leer solo las columnas necesarias desde el archivo .parquet
    df = pd.read_parquet(
        "quejas-final.parquet", columns=["barrio_localización", "tipo_solicitud", "geo_shape"]
    )
    dfvul = pd.read_csv(
        "vulnerabilidad-por-barrios.csv",
        sep=";",
        usecols=[
            "Ind_Equip",
            "Ind_Dem",
            "Ind_Econom",
            "Ind_Global",
            "Nombre",
            "Vul_Equip",
            "Vul_Dem",
            "Vul_Econom",
            "Vul_Global",
        ],
    )
    vulnerability_mapping = {
        "Vulnerabilidad Alta": 5,
        "Vulnerabilidad Media": 2.5,
        "Vulnerabilidad Baja": 1,
    }

    # Aplicar el mapeo a la columna de vulnerabilidad para crear una nueva columna
    dfvul["Nivel_Equip"] = dfvul["Vul_Equip"].map(vulnerability_mapping)
    dfvul["Nivel_Dem"] = dfvul["Vul_Dem"].map(vulnerability_mapping)
    dfvul["Nivel_Econom"] = dfvul["Vul_Econom"].map(vulnerability_mapping)
    dfvul["Nivel_Global"] = dfvul["Vul_Global"].map(vulnerability_mapping)

    # Procesar datos
    conteo_barrio_tipo = (
        df.groupby(["barrio_localización", "tipo_solicitud"]).size().reset_index(name="count")
    )
    pivot_conteo = (
        conteo_barrio_tipo.pivot(
            index="barrio_localización", columns="tipo_solicitud", values="count"
        )
        .fillna(0)
        .reset_index()
    )
    conteo_vul = pd.merge(
        pivot_conteo, dfvul, left_on="barrio_localización", right_on="Nombre", how="left"
    )

    # Filtrar columnas necesarias
    dfvul_filtrado = pd.merge(
        conteo_vul, df[["barrio_localización", "geo_shape"]], on="barrio_localización", how="left"
    )

    dfvul_filtrado["geometry"] = dfvul_filtrado["geo_shape"].apply(
        lambda x: convert_and_simplify(x)
    )

    # Crear un GeoDataFrame con las geometrías
    gdf = gpd.GeoDataFrame(dfvul_filtrado, geometry="geometry")

    # Crear un mapa base usando las geometrías
    fig = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=["List of vulnerabilities and requests by neighbourhood"],
        specs=[[{"type": "mapbox"}]],
    )

    # Añadir customdata para cada trazo
    gdf["customdata_equip"] = gdf[
        ["Ind_Equip", "Vul_Equip", "Síndic", "Sugerencia", "Queja", "Otras", "Defensor"]
    ].values.tolist()
    gdf["customdata_dem"] = gdf[
        ["Ind_Dem", "Vul_Dem", "Síndic", "Sugerencia", "Queja", "Otras", "Defensor"]
    ].values.tolist()
    gdf["customdata_econom"] = gdf[
        ["Ind_Econom", "Vul_Econom", "Síndic", "Sugerencia", "Queja", "Otras", "Defensor"]
    ].values.tolist()
    gdf["customdata_global"] = gdf[
        ["Ind_Global", "Vul_Global", "Síndic", "Sugerencia", "Queja", "Otras", "Defensor"]
    ].values.tolist()

    # Crear trazos de Choroplethmapbox para cada tipo de vulnerabilidad
    equip_trace = go.Choroplethmapbox(
        geojson=gdf.set_index("barrio_localización")["geometry"].__geo_interface__,
        locations=gdf["barrio_localización"],
        z=gdf["Nivel_Equip"],
        colorscale="YlGnBu",
        colorbar_title="Vulnerability Equipment",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=True,  # Solo el primer trazo es visible inicialmente
        customdata=gdf["customdata_equip"],
        hovertemplate="<b>Barrio:</b> %{location}<br>"
        + "<b>Vulnerability Equipment:</b> %{customdata[0]}<br>"
        + "<b>Nivel:</b> %{customdata[1]}<br>"
        + "<b>Number of Sindic:</b> %{customdata[2]}<br>"
        + "<b>Number of Suggestions:</b> %{customdata[3]}<br>"
        + "<b>Number of Complaints:</b> %{customdata[4]}<br>"
        + "<b>Number of Others:</b> %{customdata[5]}<br>"
        + "<b>Number of Defender:</b> %{customdata[6]}<extra></extra>",
    )

    dem_trace = go.Choroplethmapbox(
        geojson=gdf.set_index("barrio_localización")["geometry"].__geo_interface__,
        locations=gdf["barrio_localización"],
        z=gdf["Nivel_Dem"],
        colorscale="YlGnBu",
        colorbar_title="Demographic Vulnerability",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=False,  # Este trazo no es visible inicialmente
        customdata=gdf["customdata_dem"],
        hovertemplate="<b>Barrio:</b> %{location}<br>"
        + "<b>Demographic Vulnerability:</b> %{customdata[0]}<br>"
        + "<b>Nivel:</b> %{customdata[1]}<br>"
        + "<b>Number of Sindic::</b> %{customdata[2]}<br>"
        + "<b>Number of  Suggestions:</b> %{customdata[3]}<br>"
        + "<b>Number of  Complaints:</b> %{customdata[4]}<br>"
        + "<b>Number of  Others:</b> %{customdata[5]}<br>"
        + "<b>Number of  Defender:</b> %{customdata[6]}<extra></extra>",
    )

    eco_trace = go.Choroplethmapbox(
        geojson=gdf.set_index("barrio_localización")["geometry"].__geo_interface__,
        locations=gdf["barrio_localización"],
        z=gdf["Nivel_Econom"],
        colorscale="YlGnBu",
        colorbar_title="Vulnerabilidad Económica",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=False,  # Este trazo no es visible inicialmente
        customdata=gdf["customdata_econom"],
        hovertemplate="<b>Barrio:</b> %{location}<br>"
        + "<b>Economic Vulnerability:</b> %{customdata[0]}<br>"
        + "<b>Nivel:</b> %{customdata[1]}<br>"
        + "<b>Number of Sindic::</b> %{customdata[2]}<br>"
        + "<b>Number of  Suggestions:</b> %{customdata[3]}<br>"
        + "<b>Number of  Complaints:</b> %{customdata[4]}<br>"
        + "<b>Number of  Others:</b> %{customdata[5]}<br>"
        + "<b>Number of  Defender:</b> %{customdata[6]}<extra></extra>",
    )

    glob_trace = go.Choroplethmapbox(
        geojson=gdf.set_index("barrio_localización")["geometry"].__geo_interface__,
        locations=gdf["barrio_localización"],
        z=gdf["Nivel_Global"],
        colorscale="YlGnBu",
        colorbar_title="Global Vulnerability",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=False,  # Este trazo no es visible inicialmente
        customdata=gdf["customdata_global"],
        hovertemplate="<b>Barrio:</b> %{location}<br>"
        + "<b>Global Vulnerability: </b> %{customdata[0]}<br>"
        + "<b>Nivel:</b> %{customdata[1]}<br>"
        + "<b>Number of Sindic::</b> %{customdata[2]}<br>"
        + "<b>Number of  Suggestions:</b> %{customdata[3]}<br>"
        + "<b>Number of  Complaints:</b> %{customdata[4]}<br>"
        + "<b>Number of  Others:</b> %{customdata[5]}<br>"
        + "<b>Number of  Defender:</b> %{customdata[6]}<extra></extra>",
    )
    # Añadir trazos a la figura
    fig.add_trace(equip_trace, row=1, col=1)
    fig.add_trace(dem_trace, row=1, col=1)
    fig.add_trace(eco_trace, row=1, col=1)
    fig.add_trace(glob_trace, row=1, col=1)

    # Configuración del mapa de Valencia
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=11,
        mapbox_center={
            "lat": 39.4699,
            "lon": -0.3763,
        },  # Coordenadas para centrar el mapa en Valencia
        title_text="Vulnerability and applications",
    )

    # Configuración del menú de actualización
    fig.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {
                        "args": [{"visible": [True, False, False, False]}],
                        "label": "Equipment",
                        "method": "update",
                    },
                    {
                        "args": [{"visible": [False, True, False, False]}],
                        "label": "Demographic",
                        "method": "update",
                    },
                    {
                        "args": [{"visible": [False, False, True, False]}],
                        "label": "Economic",
                        "method": "update",
                    },
                    {
                        "args": [{"visible": [False, False, False, True]}],
                        "label": "Global",
                        "method": "update",
                    },
                ],
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": -0.3,
                "xanchor": "left",
                "y": 1.2,
                "yanchor": "top",
            }
        ]
    )

    # Convertir las columnas de vulnerabilidad a valores numéricos usando el mapeo proporcionado
    vulnerability_mapping = {
        "Vulnerabilidad Alta": 5,
        "Vulnerabilidad Media": 2.5,
        "Vulnerabilidad Baja": 1,
    }
    dfvul["Nivel_Equip"] = dfvul["Vul_Equip"].map(vulnerability_mapping)
    dfvul["Nivel_Dem"] = dfvul["Vul_Dem"].map(vulnerability_mapping)
    dfvul["Nivel_Econom"] = dfvul["Vul_Econom"].map(vulnerability_mapping)
    dfvul["Nivel_Global"] = dfvul["Vul_Global"].map(vulnerability_mapping)

    # Agrupar por distrito y calcular la media de los índices de vulnerabilidad y tomar la primera ocurrencia de las categorías
    # dfvul_agg = (
    #     dfvul.groupby("Distrito")
    #     .agg(
    #         {
    #             "Ind_Equip": "mean",
    #             "Ind_Dem": "mean",
    #             "Ind_Econom": "mean",
    #             "Ind_Global": "mean",
    #             "Vul_Equip": "first",
    #             "Vul_Dem": "first",
    #             "Vul_Econom": "first",
    #             "Vul_Global": "first",
    #         }
    #     )
    #     .reset_index()
    # )

    # Procesar datos de solicitudes
    conteo_distrito_tipo = (
        df.groupby(["distrito_localización", "tipo_solicitud"]).size().reset_index(name="count")
    )
    pivot_conteo = (
        conteo_distrito_tipo.pivot(
            index="distrito_localización", columns="tipo_solicitud", values="count"
        )
        .fillna(0)
        .reset_index()
    )
    conteo_vul = pd.merge(
        pivot_conteo, dfvul, left_on="distrito_localización", right_on="Distrito", how="left"
    )

    # Filtrar columnas necesarias
    dfvul_filtrado = pd.merge(
        conteo_vul,
        df[["distrito_localización", "geo_shape"]],
        on="distrito_localización",
        how="left",
    )

    dfvul_filtrado["geometry"] = dfvul_filtrado["geo_shape"].apply(
        lambda x: convert_and_simplify(x)
    )

    # Crear un GeoDataFrame con las geometrías
    gdf = gpd.GeoDataFrame(dfvul_filtrado, geometry="geometry")

    # Crear un mapa base usando las geometrías
    fig1 = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=["Vulnerability and applications"],
        specs=[[{"type": "mapbox"}]],
    )

    # Añadir customdata para cada trazo
    gdf["customdata_equip"] = gdf[
        ["Ind_Equip", "Vul_Equip", "Síndic", "Sugerencia", "Queja", "Otras", "Defensor"]
    ].values.tolist()
    gdf["customdata_dem"] = gdf[
        ["Ind_Dem", "Vul_Dem", "Síndic", "Sugerencia", "Queja", "Otras", "Defensor"]
    ].values.tolist()
    gdf["customdata_econom"] = gdf[
        ["Ind_Econom", "Vul_Econom", "Síndic", "Sugerencia", "Queja", "Otras", "Defensor"]
    ].values.tolist()
    gdf["customdata_global"] = gdf[
        ["Ind_Global", "Vul_Global", "Síndic", "Sugerencia", "Queja", "Otras", "Defensor"]
    ].values.tolist()

    # Crear trazos de Choroplethmapbox para cada tipo de vulnerabilidad
    equip_trace = go.Choroplethmapbox(
        geojson=gdf.set_index("distrito_localización")["geometry"].__geo_interface__,
        locations=gdf["distrito_localización"],
        z=gdf["Ind_Equip"],
        colorscale="YlGnBu",
        colorbar_title="Vulnerability Equipment",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=True,  # Solo el primer trazo es visible inicialmente
        customdata=gdf["customdata_equip"],
        hovertemplate="<b>Distrito:</b> %{location}<br>"
        + "<b>Vulnerability Equipment:</b> %{customdata[0]}<br>"
        + "<b>Nivel:</b> %{customdata[1]}<br>"
        + "<b>Number of Sindic::</b> %{customdata[2]}<br>"
        + "<b>Number of  Suggestions:</b> %{customdata[3]}<br>"
        + "<b>Number of  Complaints:</b> %{customdata[4]}<br>"
        + "<b>Number of  Others:</b> %{customdata[5]}<br>"
        + "<b>Number of  Defender:</b> %{customdata[6]}<extra></extra>",
    )

    dem_trace = go.Choroplethmapbox(
        geojson=gdf.set_index("distrito_localización")["geometry"].__geo_interface__,
        locations=gdf["distrito_localización"],
        z=gdf["Ind_Dem"],
        colorscale="YlGnBu",
        colorbar_title="Demographic Vulnerability",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=False,  # Este trazo no es visible inicialmente
        customdata=gdf["customdata_dem"],
        hovertemplate="<b>Distrito:</b> %{location}<br>"
        + "<b>Demographic Vulnerability:</b> %{customdata[0]}<br>"
        + "<b>Nivel:</b> %{customdata[1]}<br>"
        + "<b>Number of Sindic::</b> %{customdata[2]}<br>"
        + "<b>Number of  Suggestions:</b> %{customdata[3]}<br>"
        + "<b>Number of  Complaints:</b> %{customdata[4]}<br>"
        + "<b>Number of  Others:</b> %{customdata[5]}<br>"
        + "<b>Number of  Defender:</b> %{customdata[6]}<extra></extra>",
    )

    eco_trace = go.Choroplethmapbox(
        geojson=gdf.set_index("distrito_localización")["geometry"].__geo_interface__,
        locations=gdf["distrito_localización"],
        z=gdf["Ind_Econom"],
        colorscale="YlGnBu",
        colorbar_title="Economic Vulnerability",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=False,  # Este trazo no es visible inicialmente
        customdata=gdf["customdata_econom"],
        hovertemplate="<b>Distrito:</b> %{location}<br>"
        + "<b>Economic Vulnerability:</b> %{customdata[0]}<br>"
        + "<b>Nivel:</b> %{customdata[1]}<br>"
        + "<b>Number of Sindic::</b> %{customdata[2]}<br>"
        + "<b>Number of  Suggestions:</b> %{customdata[3]}<br>"
        + "<b>Number of  Complaints:</b> %{customdata[4]}<br>"
        + "<b>Number of  Others:</b> %{customdata[5]}<br>"
        + "<b>Number of  Defender:</b> %{customdata[6]}<extra></extra>",
    )

    glob_trace = go.Choroplethmapbox(
        geojson=gdf.set_index("distrito_localización")["geometry"].__geo_interface__,
        locations=gdf["distrito_localización"],
        z=gdf["Ind_Global"],
        colorscale="YlGnBu",
        colorbar_title="Global Vulnerability",
        marker_line_width=1,
        marker_opacity=0.7,
        visible=False,  # Este trazo no es visible inicialmente
        customdata=gdf["customdata_global"],
        hovertemplate="<b>Distrito:</b> %{location}<br>"
        + "<b>Global Vulnerability:</b> %{customdata[0]}<br>"
        + "<b>Nivel:</b> %{customdata[1]}<br>"
        + "<b>Number of Sindic::</b> %{customdata[2]}<br>"
        + "<b>Number of  Suggestions:</b> %{customdata[3]}<br>"
        + "<b>Number of  Complaints:</b> %{customdata[4]}<br>"
        + "<b>Number of  Others:</b> %{customdata[5]}<br>"
        + "<b>Number of  Defender:</b> %{customdata[6]}<extra></extra>",
    )

    # Añadir trazos a la figura
    fig1.add_trace(equip_trace, row=1, col=1)
    fig1.add_trace(dem_trace, row=1, col=1)
    fig1.add_trace(eco_trace, row=1, col=1)
    fig1.add_trace(glob_trace, row=1, col=1)

    # Configuración del mapa de Valencia
    fig1.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=11,
        mapbox_center={
            "lat": 39.4699,
            "lon": -0.3763,
        },  # Coordenadas para centrar el mapa en Valencia
        title_text="Vulnerability and applications",
    )

    # Configuración del menú de actualización
    fig1.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {
                        "args": [{"visible": [True, False, False, False]}],
                        "label": "Equipment",
                        "method": "update",
                    },
                    {
                        "args": [{"visible": [False, True, False, False]}],
                        "label": "Demographic",
                        "method": "update",
                    },
                    {
                        "args": [{"visible": [False, False, True, False]}],
                        "label": "Economic",
                        "method": "update",
                    },
                    {
                        "args": [{"visible": [False, False, False, True]}],
                        "label": "Global",
                        "method": "update",
                    },
                ],
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0,
                "xanchor": "left",
                "y": 1.2,
                "yanchor": "top",
            }
        ]
    )

    return [fig, fig1]
