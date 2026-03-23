import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- INTENTAR IMPORTAR LIBRERÍA DE CLICKS ---
try:
    from streamlit_plotly_events import plotly_events
    CLICK_HABILITADO = True
except ImportError:
    CLICK_HABILITADO = False
    # No mostramos cartel, solo deshabilitamos click si no está instalada.

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cenoa BI - Performance y Talento", layout="wide", page_icon="📈")

# Estilos CSS - Estética Premium y Blindaje de Botones
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] { background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.8em; font-weight: bold; border: 1px solid #c8d6e5; transition: 0.3s; font-size: 14px; }
    .metric-card { background-color: #ffffff; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA Y LIMPIEZA DE DATOS (BLINDAJE DE NULOS) ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(URL)
    # Mapeo: B=1, C=2, E=4, F=5, G=6, H=7, AG=32, AH=33
    mapping = {
        df.columns[1]: 'Vendedor', df.columns[2]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', df.columns[33]: 'Promedio'
    }
    
    meses_n = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    # Índices exactos: Ventas (I, K, M... -> 8, 10, 12...) y Alcances % (J, L, N... -> 9, 11, 13...)
    # ¡SOLUCIÓN APLICADA! Ajuste de índices para recuperar las barras
    idx_v = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30] 
    idx_p = [9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
    
    for i, mes in enumerate(meses_n):
        df[f"{mes}_v"] = pd.to_numeric(df.iloc[:, idx_v[i]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df[f"{mes}_%"] = pd.to_numeric(df.iloc[:, idx_p[i]].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)

    comp_labels = ['CRM', 'Imagen', 'Autogestión', 'Habilidad', 'Técnica']
    idx_comp = [38, 40, 42, 44, 46]
    for i, label in enumerate(comp_labels):
        df[label] = pd.to_numeric(df.iloc[:, idx_comp[i]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    df['Comp_Total_%'] = df[comp_labels].mean(axis=1).fillna(0) * 20
    df = df.rename(columns=mapping)
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], dayfirst=True, errors='coerce')
    
    for col in ['Objetivo_Mensual', 'Total_Acumulado', 'Promedio', 'Comp_Total_%']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    df = df[df['Vendedor'].astype(str).str.upper() != 'VENDEDOR']
    df['Iniciales'] = df['Vendedor'].apply(lambda x: "".join([n[0] for n in str(x).split() if n]).upper())
    df['Size_Marker'] = df['Total_Acumulado'].clip(lower=1).fillna(1)
    df['Alcance_Total_Anual'] = (df['Total_Acumulado'] / (df['Objetivo_Mensual'] * 12).replace(0, 1)) * 100
    
    return df, meses_n, comp_labels

def get_ant(fecha):
    if pd.isnull(fecha): return "Sin Dato"
    diff = datetime(2025, 12, 31) - fecha
    a, m = diff.days // 365, (diff.days % 365) // 30
    return f"{a} años y {m} meses" if a > 0 else f"{m} meses"

# --- PALETA DE COLORES 9-BOX ( solid / transparent) ---
colores_9box = {
    # Bajos
    "Bajo Rendimiento": ("#ff4c4c", "rgba(255, 76, 76, 0.1)"),
    "En Riesgo": ("#ff8c00", "rgba(255, 140, 0, 0.1)"),
    "Eficaz": ("#3cb371", "rgba(60, 179, 113, 0.2)"),
    # Medios
    "Cuestionable": ("#ffa500", "rgba(255, 165, 0, 0.1)"),
    "Core Player": ("#c8d6e5", "rgba(200, 214, 229, 0.3)"), # Gris neutro
    "High Performer": ("#32cd32", "rgba(50, 205, 50, 0.2)"),
    # Altos
    "Dilema": ("#ffc61a", "rgba(255, 198, 26, 0.1)"),
    "E. Emergente": ("#90ee90", "rgba(144, 238, 144, 0.2)"),
    "ESTRELLA": ("#008000", "rgba(0, 128, 0, 0.2)") # Deep Green
}

try:
    df_raw, lista_meses, comp_labels = load_data()
    dimension = st.sidebar.radio("MENÚ DE NAVEGACIÓN", ["Performance Comercial", "Matriz 9-Box Comercial"])

    # =========================================================
    # DIMENSIÓN 1: PERFORMANCE COMERCIAL (GRÁFICOS RESTAURADOS)
    # =========================================================
    if dimension == "Performance Comercial":
        st.markdown("### 📊 Performance Comercial Grupo Cenoa")
        
        # Filtros
        f1, f2, f3, f4 = st.columns([1, 2, 2, 1.5])
        with f1: st.selectbox("AÑO", ["2025"])
        with f2: 
            op_e = [x for x in sorted(df_raw['Empresa'].dropna().unique()) if str(x).upper() != "EMPRESA"]
            sel_emp = st.selectbox("EMPRESA", ["Todas"] + op_e)
        with f3: 
            op_l = [x for x in sorted(df_raw['Localidad'].dropna().unique()) if str(x).upper() != "LOCALIDAD"]
            sel_loc = st.selectbox("LOCALIDAD", ["Todas"] + op_l)
        
        df_p = df_raw.copy()
        if sel_emp != "Todas": df_p = df_p[df_p['Empresa'] == sel_emp]
        if sel_loc != "Todas": df_p = df_p[df_p['Localidad'] == sel_loc]
        with f4: st.metric("VENDEDORES", len(df_p))

        # Fila 1: Resumen General (RESTAURADO)
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("**Cantidad de Operaciones por Empresa**")
            df_m = df_p.groupby('Empresa')[[f"{m}_v" for m in lista_meses]].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
            df_m['Mes'] = df_m['Mes'].str.replace('_v', '')
            fig_g = px.bar(df_m, x='Mes', y='Ventas', color='Empresa', barmode='group', text_auto='.0f')
            fig_g.update_layout(xaxis=dict(type='category', categoryarray=lista_meses)) 
            st.plotly_chart(fig_g, use_container_width=True)
            
        with c2:
            st.markdown("**Top 10 Asesores (Operaciones)**")
            fig_top = px.bar(df_p.nlargest(10, 'Total_Acumulado'), x='Total_Acumulado', y='Vendedor', orientation='h', text_auto='.0f', color_discrete_sequence=['#e67e22'])
            fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)

        st.divider()
        # Análisis Individual (BARRAS RESTAURADAS)
        col_l, col_r = st.columns([1, 2.5])
        with col_l:
            v_sel = st.selectbox("🔎 Seleccionar Vendedor:", sorted(df_p['Vendedor'].unique()))
            v_data = df_p[df_p['Vendedor'] == v_sel].iloc[0]
        with col_r:
            d1, d2, d3 = st.columns([3, 1, 1])
            with d1:
                st.subheader(v_sel)
                st.markdown(f"<span style='color:#e67e22; font-weight:bold;'>{get_ant(v_data['Fecha_Ingreso'])}</span>", unsafe_allow_html=True)
                st.caption(f"{v_data['Canal']} | {v_data['Empresa']} | {v_data['Localidad']}")
            d2.metric("META", int(v_data['Objetivo_Mensual']))
            diff = v_data['Promedio'] - v_data['Objetivo_Mensual']
            d3.metric("PROM", f"{v_data['Promedio']:.1f}", delta=f"{diff:.1f}", delta_color="normal" if diff >= 0 else "inverse")
            
            # Gráfico Individual con Target
            y_vals = [float(v_data[f"{m}_v"]) for m in lista_meses]
            text_vals = [f"{v:.0f}" for v in y_vals]
            fig_evol = go.Figure()
            fig_evol.add_trace(go.Bar(x=lista_meses, y=y_vals, name="Ventas", text=text_vals, textposition='auto', marker_color='#3498db'))
            fig_evol.add_trace(go.Scatter(x=lista_meses, y=[float(v_data['Objetivo_Mensual'])]*12, mode='lines', name="Objetivo", line=dict(color='red', dash='dot', width=3)))
            fig_evol.update_layout(height=300, margin=dict(t=20), xaxis=dict(type='category', categoryorder='array', categoryarray=lista_meses))
            st.plotly_chart(fig_evol, use_container_width=True)

        # Gráficos Inferiores (Localidad y Consistencia)
        st.divider()
        g1, g2 = st.columns(2)
        with g1: 
            st.markdown("**Participación por Localidad**")
            st.plotly_chart(px.pie(df_p, values='Total_Acumulado', names='Localidad', hole=0.5), use_container_width=True)
        with g2: 
            st.markdown("**Consistencia de Ventas (Box Plot)**")
            st.plotly_chart(px.box(df_p, x='Empresa', y='Promedio', points="all", color='Empresa', hover_data=['Vendedor']), use_container_width=True)

    # =========================================================
    # DIMENSIÓN 2: MATRIZ 9-BOX (ESTÉTICA Y ARMONÍA TOTAL)
    # =========================================================
    elif dimension == "Matriz 9-Box Comercial":
        st.markdown("### 🎯 Matriz de Talento 9-Box")
        
        # Filtros Superiores
        m_f1, m_f2, m_f3 = st.columns(3)
        with m_f1: sel_p = st.selectbox("Periodo de Análisis:", ["Acumulado Anual", "Todos los meses (Promedio)"] + lista_meses)
        with m_f2: f_emp9 = st.selectbox("Empresa ", ["Todas"] + sorted(df_raw['Empresa'].dropna().unique()))
        with m_f3: f_loc9 = st.selectbox("Localidad ", ["Todas"] + sorted(df_raw['Localidad'].dropna().unique()))

        df_9 = df_raw.copy()
        if f_emp9 != "Todas": df_9 = df_9[df_9['Empresa'] == f_emp9]
        if f_loc9 != "Todas": df_9 = df_9[df_9['Localidad'] == f_loc9]
        
        # Definir Eje X según selección (Acumulado o Mes)
        df_9['X_Axis'] = df_9['Alcance_Total_Anual'] if sel_p in ["Acumulado Anual", "Todos los meses (Promedio)"] else df_9[f"{sel_p}_%"]

        # Lógica de categorías para filtros
        cat_map = {
            "Dilema": (df_9['X_Axis'] < 33.3) & (df_9['Comp_Total_%'] > 66.6),
            "E. Emergente": (df_9['X_Axis'].between(33.3, 66.6)) & (df_9['Comp_Total_%'] > 66.6),
            "ESTRELLA": (df_9['X_Axis'] >= 66.6) & (df_9['Comp_Total_%'] >= 66.6),
            "Cuestionable": (df_9['X_Axis'] < 33.3) & (df_9['Comp_Total_%'].between(33.3, 66.6)),
            "Core Player": (df_9['X_Axis'].between(33.3, 66.6)) & (df_9['Comp_Total_%'].between(33.3, 66.6)),
            "High Performer": (df_9['X_Axis'] >= 66.6) & (df_9['Comp_Total_%'].between(33.3, 66.6)),
            "Bajo Rendimiento": (df_9['X_Axis'] <= 33.3) & (df_9['Comp_Total_%'] <= 33.3),
            "En Riesgo": (df_9['X_Axis'].between(33.3, 66.6)) & (df_9['Comp_Total_%'] <= 33.3),
            "Eficaz": (df_9['X_Axis'] >= 66.6) & (df_9['Comp_Total_%'] <= 33.3)
        }

        # --- 1. BOTONES DE CATEGORÍA COLOREADOS (SOLUCIÓN ARMÓNICA) ---
        st.write("**Visualizar Listado por Categoría Comercial:**")
        cols_b1, cols_b2, cols_b3 = st.columns(3), st.columns(3), st.columns(3)
        all_cols_b = [cols_b1, cols_b2, cols_b3]
        
        if 'cat_filtrada' not in st.session_state: st.session_state.cat_filtrada = None
        
        cats_list = [
            ("Dilema", 0, 0), ("E. Emergente", 0, 1), ("ESTRELLA", 0, 2),
            ("Cuestionable", 1, 0), ("Core Player", 1, 1), ("High Performer", 1, 2),
            ("Bajo Rendimiento", 2, 0), ("En Riesgo", 2, 1), ("Eficaz", 2, 2)
        ]

        # Inyección de CSS dinámico para colorear los botones
        css_style = "<style>"
        for label, row, col in cats_list:
            solid, _ = colores_9box[label]
            # Creamos una clase única por botón basada en el label
            cls_name = f"btn-{label.replace(' ', '').replace('.','')}"
            st.markdown(f'<div class="{cls_name}">', unsafe_allow_html=True)
            if all_cols_b[row][col].button(label, key=f"b_{label}", use_container_width=True):
                st.session_state.cat_filtrada = label
            st.markdown('</div>', unsafe_allow_html=True)
            
            # CSS para colorear: borde sólido, fondo suave, texto sólido.
            # Estrella necesita texto blanco.
            txt_col = "white" if label == "ESTRELLA" else solid
            css_style += f"""
                .{cls_name} > button {{
                    border: 2px solid {solid} !important;
                    color: {txt_col} !important;
                    background-color: { solid if label == "ESTRELLA" else "white" } !important;
                }}
                .{cls_name} > button:hover {{
                    background-color: {solid} !important;
                    color: white !important;
                }}
            """
        css_style += "</style>"
        st.markdown(css_style, unsafe_allow_html=True)

        # DESPLEGAR TABLA CON BOTÓN DE CERRAR
        if st.session_state.cat_filtrada:
            st.divider()
            col_t1, col_t2 = st.columns([4, 1])
            col_t1.markdown(f"#### 📋 Asesores en Categoría: **{st.session_state.cat_filtrada}**")
            with col_t2:
                if st.button("❌ Cerrar Listado", key="btn_cerrar", use_container_width=True):
                    st.session_state.cat_filtrada = None
                    st.rerun() 
                    
            df_detalle = df_9[cat_map[st.session_state.cat_filtrada]]
            st.dataframe(df_detalle[['Vendedor', 'Empresa', 'Localidad', 'X_Axis', 'Comp_Total_%']].rename(columns={'X_Axis': '% Resultados', 'Comp_Total_%': '% Competencias'}), use_container_width=True)
            st.divider()

        # --- 2. GRÁFICO MATRIZ MEJORADO ESTÉTICAMENTE (COLORES DE FONDO) ---
        fig_9 = px.scatter(
            df_9, x='X_Axis', y='Comp_Total_%', text='Iniciales', color='Empresa',
            size='Size_Marker', hover_name='Vendedor',
            range_x=[-5, 130], range_y=[-5, 110],
            labels={'X_Axis': f'% Resultados ({sel_p})', 'Comp_Total_%': '% Competencias'},
            height=650, template="plotly_white"
        )
        # Formato de las esferas (texto blanco, bordes definidos)
        fig_9.update_traces(textposition='middle center', textfont=dict(color='white', size=11), marker=dict(opacity=0.85, line=dict(width=1.5, color='DarkSlateGrey')))
        
        # AGREGAR FONDOS DE COLORES A LOS 9 CUADRANTES
        for label, (solid, trans) in colores_9box.items():
            # Definir coordenadas según la lógica de la 9-box
            if label in ["Dilema", "Cuestionable", "Bajo Rendimiento"]: x0, x1 = -5, 33.3
            elif label in ["E. Emergente", "Core Player", "En Riesgo"]: x0, x1 = 33.3, 66.6
            else: x0, x1 = 66.6, 130 # Altos

            if label in ["Bajo Rendimiento", "En Riesgo", "Eficaz"]: y0, y1 = -5, 33.3
            elif label in ["Cuestionable", "Core Player", "High Performer"]: y0, y1 = 33.3, 66.6
            else: y0, y1 = 66.6, 110 # Altos

            fig_9.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=trans, layer="below", line_width=0)
        
        # Líneas de división más suaves
        fig_9.add_vline(x=33.3, line_dash="dash", line_color="rgba(0,0,0,0.2)")
        fig_9.add_vline(x=66.6, line_dash="dash", line_color="rgba(0,0,0,0.2)")
        fig_9.add_hline(y=33.3, line_dash="dash", line_color="rgba(0,0,0,0.2)")
        fig_9.add_hline(y=66.6, line_dash="dash", line_color="rgba(0,0,0,0.2)")
        
        # Eliminar leyenda de empresa para limpiar el gráfico si es muy grande
        fig_9.update_layout(showlegend=False)

        # --- 3. INTERACTIVIDAD DE CLICKS Y FICHA TÉCNICA (Blindada) ---
        vendedor_seleccionado = None
        
        if CLICK_HABILITADO:
            st.caption("👈 **Haz click en una esfera** para ver la ficha técnica del vendedor.")
            puntos_click = plotly_events(fig_9, click_event=True, hover_event=False)
            
            if len(puntos_click) > 0:
                click_x = puntos_click[0]['x']
                click_y = puntos_click[0]['y']
                # Blindaje de coincidencia por decimales
                match = df_9[(df_9['X_Axis'].round(1) == round(click_x, 1)) & (df_9['Comp_Total_%'].round(1) == round(click_y, 1))]
                if not match.empty:
                    vendedor_seleccionado = match.iloc[0]['Vendedor']
        else:
            st.plotly_chart(fig_9, use_container_width=True)
            
        st.divider()
        # Buscador Manual Sincronizado
        opciones_vendedores = ["-- Seleccionar Asesor --"] + sorted(df_9['Vendedor'].unique())
        idx_defecto = opciones_vendedores.index(vendedor_seleccionado) if vendedor_seleccionado in opciones_vendedores else 0
        
        st.markdown("### 📋 Ficha Técnica de Desempeño")
        v_ficha = st.selectbox("🔎 Buscador Manual de Asesor:", opciones_vendedores, index=idx_defecto)

        # 4. DESGLOSE DE FICHA TÉCNICA
        if v_ficha != "-- Seleccionar Asesor --":
            v_f = df_9[df_9['Vendedor'] == v_ficha].iloc[0]
            
            # Tarjetas Superiores
            k1, k2, k3 = st.columns(3)
            with k1: st.markdown(f"<div class='metric-card'><h2>{v_f['X_Axis']:.1f}%</h2><p>RESULTADOS ({sel_p})</p></div>", unsafe_allow_html=True)
            with k2: st.markdown(f"<div class='metric-card'><h2>{v_f['Comp_Total_%']:.1f}%</h2><p>COMPETENCIAS</p></div>", unsafe_allow_html=True)
            with k3:
                # Determinar cuadrante para el color
                solid_col = "#e67e22" # Default naranja (Core)
                estado_txt = "EN DESARROLLO 📈"
                if v_f['X_Axis'] >= 66.6 and v_f['Comp_Total_%'] >= 66.6:
                    solid_col = "#008000" # Verde (Estrella)
                    estado_txt = "MIEMBRO CLAVE 🌟"
                elif v_f['X_Axis'] <= 33.3 and v_f['Comp_Total_%'] <= 33.3:
                    solid_col = "#ff4c4c" # Rojo (Bajo)
                    estado_txt = "RIESGO ALTO 🚨"
                
                st.markdown(f"<div class='metric-card' style='border-top: 5px solid {solid_col};'><h2 style='color:{solid_col};'>{estado_txt}</h2><p>ESTADO ACTUAL</p></div>", unsafe_allow_html=True)

            # Gráficos Radar y Línea
            gl, gr = st.columns([1, 1.5])
            with gl:
                st.markdown("**Desglose de Competencias**")
                # CONVERSIÓN DE COMPETENCIAS A PORCENTAJE (Base 20 para llegar a 100)
                comp_pcts = [v_f[c] * 20 for c in comp_labels]
                fig_c = px.bar(x=comp_pcts, y=comp_labels, orientation='h', color=comp_labels, text=[f"{val:.1f}%" for val in comp_pcts])
                fig_c.update_layout(showlegend=False, xaxis_range=[0, max(comp_pcts + [100]) + 10], xaxis_title="Nivel (%)", yaxis_title="") 
                st.plotly_chart(fig_c, use_container_width=True)
            with gr:
                st.markdown("**Evolución mensual % alcance de ventas**")
                alcances = [v_f[f"{m}_%"] for m in lista_meses]
                fig_l = px.line(x=lista_meses, y=alcances, markers=True, text=[f"{val:.0f}%" for val in alcances])
                fig_l.update_traces(line_color='#2ecc71', line_width=4, marker=dict(size=10, color='white', line=dict(width=2, color='#2ecc71')))
                fig_l.update_layout(yaxis_range=[0, max(alcances)+20])
                st.plotly_chart(fig_l, use_container_width=True)

except Exception as e:
    st.error(f"Falla crítica: {e}")
