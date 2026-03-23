import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Cenoa Performance Pro", layout="wide")
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRUIM7cEzymYekqDN9I4Jyd0o9peeJh5izcTtFFHPDzxBmt1zWJxa3gyD8hDMBLDw/pub?output=csv"

@st.cache_data
def load_data_robust(url):
    df = pd.read_csv(url)
    # Limpiamos nombres de columnas (minúsculas y sin espacios)
    df.columns = df.columns.str.strip().str.lower()
    # Eliminamos columnas vacías
    df = df.loc[:, ~df.columns.str.contains('^unnamed')]
    return df

def find_column(df, keywords):
    """Busca una columna que contenga alguna de las palabras clave."""
    for col in df.columns:
        if any(key in col for key in keywords):
            return col
    return None

st.title("🚗 Performance Comercial: Grupo Cenoa")

try:
    df = load_data_robust(CSV_URL)
    
    # --- AUTO-DETECCIÓN DE COLUMNAS ---
    col_vendedor = find_column(df, ['nombre', 'vendedor', 'asesor'])
    col_ventas = find_column(df, ['ventas', 'real', 'vta'])
    col_objetivo = find_column(df, ['objetivo', 'meta', 'cuota', 'obj'])
    col_competencias = find_column(df, ['competencias', 'comportamiento', 'soft'])

    if not col_vendedor or not col_ventas or not col_objetivo:
        st.error("⚠️ No pudimos identificar las columnas básicas automáticamente.")
        st.write("Columnas encontradas en tu archivo:", list(df.columns))
        st.info("Asegúrate de que las columnas tengan nombres como: 'Vendedor', 'Ventas' y 'Objetivo'.")
        st.stop()

    # --- LIMPIEZA DE DATOS ---
    for c in [col_ventas, col_objetivo, col_competencias]:
        if c:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    # --- FILTROS ---
    st.sidebar.header("Configuración")
    vendedores = st.sidebar.multiselect("Filtrar Asesores", options=sorted(df[col_vendedor].unique()), default=df[col_vendedor].unique())
    df_filtered = df[df[col_vendedor].isin(vendedores)].copy()

    # --- CÁLCULO DE MÉTRICAS ---
    df_filtered['% cumpl.'] = (df_filtered[col_ventas] / df_filtered[col_objetivo].replace(0, 1) * 100).round(1)

    # --- DASHBOARD ---
    k1, k2, k3 = st.columns(3)
    k1.metric("Ventas Totales", f"{df_filtered[col_ventas].sum():,.0f}")
    k2.metric("Objetivo Total", f"{df_filtered[col_objetivo].sum():,.0f}")
    cumpl_total = (df_filtered[col_ventas].sum() / df_filtered[col_objetivo].sum() * 100) if df_filtered[col_objetivo].sum() > 0 else 0
    k3.metric("% Cumplimiento Global", f"{cumpl_total:.1f}%")

    st.divider()

    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📊 Ranking por Cumplimiento")
        fig_bar = px.bar(
            df_filtered.sort_values('% cumpl.', ascending=True).tail(12),
            x='% cumpl.', y=col_vendedor, orientation='h',
            text='% cumpl.', color='% cumpl.',
            color_continuous_scale='RdYlGn',
            labels={'% cumpl.': '% Cumplimiento', col_vendedor: 'Asesor'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.subheader("🎯 Matriz de Performance")
        # Si existe columna de competencias, la usamos para el eje X, sino usamos objetivos
        x_axis = col_competencias if col_competencias else col_objetivo
        fig_scatter = px.scatter(
            df_filtered, x=x_axis, y=col_ventas,
            size='% cumpl.', color='% cumpl.',
            hover_name=col_vendedor,
            color_continuous_scale='Viridis',
            labels={x_axis: 'Competencias / Meta', col_ventas: 'Ventas Reales'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with st.expander("🔍 Ver Tabla de Datos"):
        st.dataframe(df_filtered)

except Exception as e:
    st.error(f"Falla en el procesamiento: {e}")
