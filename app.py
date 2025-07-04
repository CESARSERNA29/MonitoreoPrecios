
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from io import BytesIO

st.set_page_config(page_title="Tablero de Precios", layout="wide")
st.markdown("""
    <style>
        .main {background-color: #f4f6f9;}
        .stButton>button {background-color: #4CAF50; color: white; font-weight: bold;}
        .stMetric {font-size: 18px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

st.title("📊 Monitoreo de Precios por Producto")
st.markdown("Visualiza la evolución de precios mensuales, define límites de control y exporta resultados.")
st.markdown("---")

github_url = "https://raw.githubusercontent.com/mi-usuario/mi-repo/main/data/precios_productos_demo.xlsx"

try:
    response = requests.get(github_url)
    df = pd.read_excel(BytesIO(response.content))
    df["periodo"] = pd.to_datetime(df["periodo"])
    df = df.sort_values("periodo")

    st.sidebar.header("🎛️ Filtros")
    area_opciones = sorted(df["AreaMetropolitana"].dropna().unique())
    canal_opciones = sorted(df["Canal"].dropna().unique())
    producto_ids = sorted(df["producto_id"].dropna().unique())

    area_sel = st.sidebar.multiselect("Área Metropolitana:", area_opciones, default=area_opciones)
    canal_sel = st.sidebar.multiselect("Canal de Comercialización:", canal_opciones, default=canal_opciones)
    producto_id_sel = st.sidebar.multiselect("ID de Producto:", producto_ids, default=producto_ids)

    df_filtrado = df[
        (df["AreaMetropolitana"].isin(area_sel)) &
        (df["Canal"].isin(canal_sel)) &
        (df["producto_id"].isin(producto_id_sel))
    ]

    productos = sorted(df_filtrado["producto_nombre"].unique())
    seleccionados = st.multiselect("🛒 Selecciona productos a visualizar:", productos, default=productos[:3])

    limites_dict = {}
    fig = go.Figure()

    for prod in seleccionados:
        df_prod = df_filtrado[df_filtrado["producto_nombre"] == prod]
        col1, col2 = st.columns(2)
        with col1:
            lim_inf = st.number_input(f"🔻 Límite inferior - {prod}", min_value=0, value=int(df_prod["precio"].min() * 0.9))
        with col2:
            lim_sup = st.number_input(f"🔺 Límite superior - {prod}", min_value=0, value=int(df_prod["precio"].max() * 1.1))

        limites_dict[prod] = {"inferior": lim_inf, "superior": lim_sup}
        fuera_rango = df_prod[(df_prod["precio"] < lim_inf) | (df_prod["precio"] > lim_sup)]

        fig.add_trace(go.Scatter(x=df_prod["periodo"], y=df_prod["precio"], mode="lines+markers", name=f"{prod} - Precio"))
        fig.add_trace(go.Scatter(x=df_prod["periodo"], y=[lim_sup]*len(df_prod), mode="lines", name=f"{prod} - Límite Superior", line=dict(color="red", dash="dash")))
        fig.add_trace(go.Scatter(x=df_prod["periodo"], y=[lim_inf]*len(df_prod), mode="lines", name=f"{prod} - Límite Inferior", line=dict(color="green", dash="dash")))
        fig.add_trace(go.Scatter(x=fuera_rango["periodo"], y=fuera_rango["precio"], mode="markers", name=f"{prod} - ⚠ Fuera de Rango", marker=dict(color="orange", size=10, symbol="x")))

    fig.update_layout(title="📈 Evolución de Precios con Límites de Control", xaxis_title="Periodo", yaxis_title="Precio", hovermode="x unified", height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 💾 Guardar límites definidos")
    nombre_archivo = st.text_input("Nombre del archivo a guardar:", value="limites_guardados")
    if st.button("Guardar límites como CSV"):
        limites_df = pd.DataFrame.from_dict(limites_dict, orient="index").reset_index()
        limites_df.columns = ["producto_nombre", "limite_inferior", "limite_superior"]
        limites_df.to_csv(f"{nombre_archivo}.csv", index=False)
        st.success(f"✅ Límites guardados exitosamente como '{nombre_archivo}.csv'.")

    st.markdown("---")
    st.subheader("🧾 Tabla de Datos Filtrados")
    st.dataframe(df_filtrado[df_filtrado["producto_nombre"].isin(seleccionados)].sort_values(["producto_nombre", "periodo"]))

except Exception as e:
    st.error("❌ Error al cargar datos desde GitHub. Verifica la URL o conexión.")
    st.exception(e)
