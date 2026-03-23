import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Performance Comercial Grupo Cenoa", layout="wide", page_icon="🚗")

# Estilo para imitar la interfaz del ejemplo
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] { background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; }
    .vendedor-card { border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 5px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(URL)
    # Mapeo preciso de columnas
    mapping = {
        df.columns[1]: 'Vendedor', df.columns[3]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', df.columns[33]: 'Promedio'
    }
    df = df.rename(columns=mapping)
    
    # Extraer meses (Col 8 a 19 -> I a T)
    meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    for i, mes in enumerate(meses_nombres):
        df[mes] = pd.to_numeric(df.iloc[:, 8+i].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    # Limpieza de valores clave
    for c in ['Objetivo_Mensual', 'Total_Acumulado', 'Promedio']:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], errors='coerce')
    return df, meses_nombres

try:
    df_raw, lista_meses = load_data()

    # --- HEADER / FILTROS SUPERIORES ---
    h1, h2, h3, h4, h5 = st.columns([3, 1, 1.5, 1.5, 1])
    with h1: st.title("Performance Comercial Grupo Cenoa")
    with h2: st.selectbox("AÑO", ["2025"])
    with h3: f_empresa = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw['Empresa'].dropna().unique().tolist()))
    with h4: f_localidad = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw['Localidad'].dropna().unique().tolist()))
    with h5: st.metric("", f"👥 {len(df_raw)}")

    # Filtrado
    df = df_raw.copy()
    if f_empresa != "Todas": df = df[df['Empresa'] == f_empresa]
    if f_localidad != "Todas": df = df[df['Localidad'] == f_localidad]

    # --- FILA 1: GRÁFICOS GENERALES ---
    c1, c2 = st.columns([1.5, 1])

    with c1:
        st.markdown("**Cantidad de Operaciones por Empresa**")
        df_melt = df.groupby('Empresa')[lista_meses].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
        fig_gen = px.bar(df_melt, x='Mes', y='Ventas', color_discrete_sequence=['#3498db'], text_auto='.0f')
        # Forzar orden de meses
        fig_gen.update_xaxes(categoryorder='array', categoryarray=lista_meses)
        fig_gen.update_layout(height=300, margin=dict(t=10, b=10), showlegend=False)
        st.plotly_chart(fig_gen, use_container_width=True)

    with c2:
        st.markdown("**Top 10 Vendedores (Operaciones)**")
        top_10 = df.nlargest(10, 'Total_Acumulado')
        fig_top = px.bar(top_10, x='Total_Acumulado', y='Vendedor', orientation='h', text_auto='.0f', color_discrete_sequence=['#e67e22'])
        fig_top.update_layout(height=300, margin=dict(t=10, b=10), yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)

    # --- FILA 2: DETALLE INDIVIDUAL (LISTA + GRÁFICO) ---
    st.divider()
    col_lista, col_detalle = st.columns([1, 2.5])

    with col_lista:
        st.markdown("**Seleccionar Vendedor**")
        # Buscador de texto
        search = st.text_input("Buscar...", label_visibility="collapsed")
        df_list = df[df['Vendedor'].str.contains(search, case=False)] if search else df
        
        # Lista de selección (usamos un radio con estilo de lista)
        vendedor_sel = st.radio("Lista de Vendedores", options=df_list['Vendedor'].tolist(), label_visibility="collapsed")

    with col_detalle:
        v_data = df_raw[df_raw['Vendedor'] == vendedor_sel].iloc[0]
        
        # Header del Vendedor Seleccionado
        d_cab, d_met = st.columns([3, 1])
        with d_cab:
            st.subheader(vendedor_sel)
            st.caption(f"{v_data['Canal']} | {v_data['Empresa']}")
            # Antigüedad
            hoy = datetime(2025, 12, 31)
            ant = hoy - v_data['Fecha_Ingreso']
            st.markdown(f"<span style='color:orange; font-weight:bold;'>{ant.days // 365} Años {(ant.days % 365) // 30} Meses</span>", unsafe_allow_html=True)
        
        with d_met:
            m_obj, m_prom = st.columns(2)
            m_obj.metric("OBJ", int(v_data['Objetivo_Mensual']))
            # Semáforo en Promedio
            diff = v_data['Promedio'] - v_data['Objetivo_Mensual']
            m_prom.metric("PROM", f"{v_data['Promedio']:.1f}", delta=f"{diff:.1f}", delta_color="normal" if diff >= 0 else "inverse")

        # GRÁFICO DE EVOLUCIÓN (MESES SIEMPRE VISIBLES)
        ventas_vals = [v_data[m] for m in lista_meses]
        fig_ind = go.Figure()
        # Barras de Ventas
        fig_ind.add_trace(go.Bar(
            x=lista_meses, y=ventas_vals, name="Ventas", 
            marker_color='#3498db', text=ventas_vals, textposition='auto'
        ))
        # Línea de Objetivo (Target)
        fig_ind.add_trace(go.Scatter(
            x=lista_meses, y=[v_data['Objetivo_Mensual']]*12, 
            mode='lines', name="Objetivo", line=dict(color='red', width=2, dash='dot')
        ))
        
        fig_ind.update_layout(
            height=300, margin=dict(t=20, b=20),
            xaxis=dict(type='category', categoryorder='array', categoryarray=lista_meses), # FORZAR LOS 12 MESES
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_ind, use_container_width=True)
        st.write(f"📍 Localidad: {v_data['Localidad']} | Canal: {v_data['Canal']}")

except Exception as e:
    st.error(f"Error en la visualización: {e}")
