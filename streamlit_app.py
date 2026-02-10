import streamlit as st
import pandas as pd
import string
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title='Dashboard Logístico', layout='wide')
st.title('📊 Dashboard de Auditoría Logística')

# --- BARRA LATERAL ---
st.sidebar.header('Configuración')
uploaded_file = st.sidebar.file_uploader('Cargar archivo Excel', type=['xlsx'])
top_n_cp = st.sidebar.slider('Códigos Postales a mostrar (Tab 2)', min_value=5, max_value=50, value=10)

if uploaded_file is not None:
    # 1. Preparación de datos
    column_names = list(string.ascii_uppercase[:17])
    df = pd.read_excel(uploaded_file, names=column_names, header=0)
    
    df['CP_Limpio'] = df['O'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df['H'] = df['H'].astype(str).str.strip()
    
    mask_exito = (df['L'].astype(str).str.contains('entregado', case=False, na=False) | 
                  df['L'].astype(str).str.contains('efectividad', case=False, na=False))
    
    total_envios = len(df)
    total_exitos = len(df[mask_exito])
    efectividad_global = (total_exitos / total_envios * 100) if total_envios > 0 else 0

    st.markdown('### 📈 Resumen Operativo Global')
    c1, c2, c3 = st.columns(3)
    c1.metric('Total Envíos', f"{total_envios} env.")
    c2.metric('Envíos Entregados', f"{total_exitos} env.")
    c3.metric('Efectividad Global', f"{efectividad_global:.1f}%")
    st.progress(efectividad_global / 100)
    st.divider()

    tab1, tab2, tab3 = st.tabs(['🚚 Rendimiento (Top 5 vs 5)', '📍 Geografía (CP)', '⚠️ Auditoría de Incidencias'])

    # --- TAB 1: MEJORES VS PEORES (LÍNEAS) ---
    with tab1:
        st.subheader('🚀 Comparativa de Extremos: Efectividad')
        rep_total = df['H'].value_counts().reset_index()
        rep_total.columns = ['Repartidor', 'Total']
        rep_exitos = df[mask_exito]['H'].value_counts().reset_index()
        rep_exitos.columns = ['Repartidor', 'Exitos']
        resumen_repa = pd.merge(rep_total, rep_exitos, on='Repartidor', how='left').fillna(0)
        resumen_repa['% Efectividad'] = (resumen_repa['Exitos'] / resumen_repa['Total'] * 100).round(1)
        
        mejores = resumen_repa.sort_values('% Efectividad', ascending=False).head(5)
        peores = resumen_repa.sort_values('% Efectividad', ascending=True).head(5)

        col_m, col_p = st.columns(2)
        with col_m:
            fig_m = px.line(mejores, x='Repartidor', y='% Efectividad', text='% Efectividad', markers=True, title='Top 5 Excelencia')
            fig_m.update_traces(line_color='green', textposition='top center')
            st.plotly_chart(fig_m, use_container_width=True)
        with col_p:
            fig_p = px.line(peores, x='Repartidor', y='% Efectividad', text='% Efectividad', markers=True, title='Top 5 Críticos')
            fig_p.update_traces(line_color='red', textposition='top center')
            st.plotly_chart(fig_p, use_container_width=True)

    # --- TAB 2: GEOGRAFÍA ---
    with tab2:
        st.subheader(f'📍 Distribución por CP (Top {top_n_cp})')
        cp_counts = df['CP_Limpio'].value_counts().reset_index()
        cp_counts.columns = ['CP', 'Cantidad']
        cp_counts['Porcentaje'] = (cp_counts['Cantidad'] / total_envios * 100).round(1)
        cp_counts['Etiqueta'] = cp_counts.apply(lambda x: f"{int(x['Cantidad'])} | {x['Porcentaje']}%", axis=1)
        fig_cp = px.bar(cp_counts.head(top_n_cp), x='CP', y='Cantidad', text='Etiqueta', color='Cantidad', color_continuous_scale='Blues')
        st.plotly_chart(fig_cp, use_container_width=True)

    # --- TAB 3: AUDITORÍA CON TOTALIZADO ---
    with tab3:
        st.subheader('🔥 Auditoría General: Detalle de Incidencias')
        
        # 1. Pivotar incidencias
        inc_data = df.groupby(['H', 'L']).size().reset_index(name='Cant')
        pivot_inc = inc_data.pivot(index='H', columns='L', values='Cant').fillna(0)
        
        # 2. Identificar y separar la columna de éxito (Entregado) para el cálculo de incidencias puras
        col_exito = next((c for c in pivot_inc.columns if "entregado" in str(c).lower() or "efectividad" in str(c).lower()), None)
        cols_incidencias_puras = [c for c in pivot_inc.columns if c != col_exito]
        
        # 3. Crear el Total de Incidencias (suma de todas las columnas de error)
        pivot_inc['TOTAL INCIDENCIAS'] = pivot_inc[cols_incidencias_puras].sum(axis=1)
        
        # 4. Unir con porcentajes y ordenar
        resumen_repa['% Incidencias'] = (100 - resumen_repa['% Efectividad']).round(1)
        rep_stats = resumen_repa.set_index('Repartidor')[['% Efectividad', '% Incidencias']]
        auditoria_final = rep_stats.merge(pivot_inc, left_index=True, right_index=True, how='left').fillna(0)
        
        # Ordenar por % Incidencias (Peores primero)
        auditoria_final = auditoria_final.sort_values('% Incidencias', ascending=False)

        # 5. Visualización
        altura = max(8, len(auditoria_final) * 0.4)
        fig_aud, ax_aud = plt.subplots(figsize=(16, altura))
        
        # Mapa de calor: Usamos un formato de anotación 'g' para que los totales grandes se lean bien
        sns.heatmap(auditoria_final,

