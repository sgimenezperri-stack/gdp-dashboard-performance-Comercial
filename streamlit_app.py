import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cenoa BI - Sistema Integral", layout="wide", page_icon="📊")

# Estilos CSS Profesionales
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] { background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .analisis-box { background-color: #e8f4f8; padding: 15px; border-left: 5px solid #3498db; border-radius: 5px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA Y LIMPIEZA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(URL)
    # Mapeo según estructura solicitada
    mapping = {
        df.columns[1]: 'Vendedor', df.columns[2]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', df.columns[33]: 'Promedio'
    }
    
    # 1. Resultados (Ventas) - Columnas J a AF (saltadas)
    idx_res = [9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    for i, idx in enumerate(idx_res):
        df[meses[i]] = pd.to_numeric(df.iloc[:, idx].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    # 2. Competencias - Columnas AM a AW (saltadas)
    idx_comp = [38, 40, 42, 44, 46, 48]
    df['Score_Comp'] = df.iloc[:, idx_comp].apply(pd.to_numeric, errors='coerce').mean(axis=1).fillna(0)
    df['Comp_Porc'] = (df['Score_Comp'] / 5) * 100 # Asumiendo escala 1-5
    
    df = df.rename(columns=mapping)
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], dayfirst=True, errors='coerce')
    # Limpiar filas de títulos o vacías
    df = df[df['Vendedor'].astype(str).str.upper() != 'VENDEDOR']
    
    # Limpieza final de numéricos para evitar el error de Matriz
    for c in ['Objetivo_Mensual', 'Total_Acumulado', 'Promedio', 'Comp_Porc']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        
    return df, meses

try:
    df_raw, lista_meses = load_data()

    # --- MENÚ LATERAL ---
    st.sidebar.title("Menú de Navegación")
    dimension = st.sidebar.radio("Ir a:", ["Performance Comercial", "Matriz 9-Box Comercial"])

    # ---------------------------------------------------------
    # DIMENSIÓN: PERFORMANCE COMERCIAL (Restaurada)
    # ---------------------------------------------------------
    if dimension == "Performance Comercial":
        st.markdown("### 📊 Performance Comercial Grupo Cenoa")
        
        # Filtros Superiores (Como en image_5b3c26)
        f_col1, f_col2, f_col3, f_col4 = st.columns([1, 2, 2, 1.5])
        with f_col1: st.selectbox("AÑO", ["2025"])
        with f_col2: 
            op_emp = [x for x in sorted(df_raw['Empresa'].dropna().unique()) if str(x).upper() != "EMPRESA"]
            f_emp = st.selectbox("EMPRESA", ["Todas"] + op_emp)
        with f_col3: 
            op_loc = [x for x in sorted(df_raw['Localidad'].dropna().unique()) if str(x).upper() != "LOCALIDAD"]
            f_loc = st.selectbox("LOCALIDAD", ["Todas"] + op_loc)
        
        # Filtrado Dinámico
        df_f = df_raw.copy()
        if f_emp != "Todas": df_f = df_f[df_f['Empresa'] == f_emp]
        if f_loc != "Todas": df_f = df_f[df_f['Localidad'] == f_loc]
        
        with f_col4: st.metric("VENDEDORES", len(df_f))

        # Fila 1: Gráficos Acumulados
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("**Cantidad de Operaciones por Empresa**")
            df_m = df_f.groupby('Empresa')[lista_meses].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
            fig_g = px.bar(df_m, x='Mes', y='Ventas', color='Empresa', barmode='group', text_auto='.0f', color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_g.update_xaxes(categoryorder='array', categoryarray=lista_meses)
            st.plotly_chart(fig_g, use_container_width=True)
        with c2:
            st.markdown("**Top 10 Vendedores (Acumulado)**")
            st.plotly_chart(px.bar(df_f.nlargest(10, 'Total_Acumulado'), x='Total_Acumulado', y='Vendedor', orientation='h', text_auto='.0f', color_discrete_sequence=['#e67e22']), use_container_width=True)

        st.divider()
        
        # Análisis Individual
        col_l, col_r = st.columns([1, 2.5])
        with col_l:
            v_sel = st.selectbox("Seleccionar Vendedor:", sorted(df_f['Vendedor'].unique()))
            v_data = df_f[df_f['Vendedor'] == v_sel].iloc[0]
        
        with col_r:
            d1, d2, d3 = st.columns([2.5, 1, 1])
            with d1:
                st.subheader(v_sel)
                # Antigüedad dinámica
                hoy = datetime(2025, 12, 31)
                ant = hoy - v_data['Fecha_Ingreso']
                st.markdown(f"🗓️ **Antigüedad:** <span style='color:#e67e22; font-weight:bold;'>{ant.days // 365} años y {(ant.days % 365) // 30} meses</span>", unsafe_allow_html=True)
                st.caption(f"{v_data['Canal']} | {v_data['Empresa']} | {v_data['Localidad']}")
            
            diff = v_data['Promedio'] - v_data['Objetivo_Mensual']
            d2.metric("META", f"{v_data['Objetivo_Mensual']:,.0f}")
            d3.metric("PROM", f"{v_data['Promedio']:,.1f}", delta=f"{diff:.1f}", delta_color="normal" if diff >= 0 else "inverse")

            # Evolución con Target
            fig_i = go.Figure()
            fig_i.add_trace(go.Bar(x=lista_meses, y=[v_data[m] for m in lista_meses], name="Ventas", marker_color='#3498db', text_auto='.0f'))
            fig_i.add_trace(go.Scatter(x=lista_meses, y=[v_data['Objetivo_Mensual']]*12, mode='lines', name="Target", line=dict(color='red', dash='dot')))
            fig_i.update_layout(height=300, margin=dict(t=20), xaxis=dict(type='category', categoryorder='array', categoryarray=lista_meses))
            st.plotly_chart(fig_i, use_container_width=True)

        # Gráficos Pie y Box
        st.divider()
        g1, g2 = st.columns(2)
        with g1: 
            st.markdown("**Localidad**")
            st.plotly_chart(px.pie(df_f, values='Total_Acumulado', names='Localidad', hole=0.5), use_container_width=True)
        with g2: 
            st.markdown("**Consistencia**")
            st.plotly_chart(px.box(df_f, x='Empresa', y='Promedio', points="all", color='Empresa', hover_data=['Vendedor']), use_container_width=True)

    # ---------------------------------------------------------
    # DIMENSIÓN: MATRIZ 9-BOX (Corregida)
    # ---------------------------------------------------------
    elif dimension == "Matriz 9-Box Comercial":
        st.markdown("### 🎯 Matriz de Talento 9-Box")
        
        # Corrección del Error NaN: Aseguramos que el tamaño sea > 0 y no nulo
        df_9 = df_raw.copy()
        max_v = df_9['Total_Acumulado'].max() if df_9['Total_Acumulado'].max() > 0 else 1
        df_9['Ventas_Porc'] = (df_9['Total_Acumulado'] / max_v) * 100
        
        # Filtro para el gráfico: Quitar ceros absolutos si es necesario para el tamaño
        df_9_plot = df_9[df_9['Total_Acumulado'] >= 0].copy()

        fig_9 = px.scatter(
            df_9_plot, x='Ventas_Porc', y='Comp_Porc',
            text='Vendedor', color='Empresa',
            size='Total_Acumulado', # El fix es el fillna(0) que hicimos en load_data
            range_x=[0, 105], range_y=[0, 105],
            labels={'Ventas_Porc': 'Resultados (%)', 'Comp_Porc': 'Competencias (%)'},
            height=700, template="plotly_white"
        )

        # Líneas de Cuadrantes
        fig_9.add_vline(x=33.3, line_dash="dot", line_color="gray")
        fig_9.add_vline(x=66.6, line_dash="dot", line_color="gray")
        fig_9.add_hline(y=33.3, line_dash="dot", line_color="gray")
        fig_9.add_hline(y=66.6, line_dash="dot", line_color="gray")

        # Etiquetas de Fondo
        labels = [(15, 85, "Dilema"), (50, 85, "Estrella Emergente"), (85, 85, "ESTRELLA"),
                  (15, 50, "Cuestionable"), (50, 50, "Core Player"), (85, 50, "High Performer"),
                  (15, 15, "Bajo Rendimiento"), (50, 15, "En Riesgo"), (85, 15, "Eficaz")]
        for x, y, txt in labels:
            fig_9.add_annotation(x=x, y=y, text=txt, showarrow=False, font=dict(color="rgba(0,0,0,0.1)"))

        st.plotly_chart(fig_9, use_container_width=True)

except Exception as e:
    st.error(f"Falla crítica: {e}")
