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
top_n_repa = st.sidebar.slider('Repartidores a mostrar (Tab 1)', min_value=5, max_value=30, value=10)
top_n_cp = st.sidebar.slider('Códigos Postales a mostrar (Tab 2)', min_value=5, max_value=50, value=10)

if uploaded_file is not None:
    # 1. Preparación de datos
    column_names = list(string.ascii_uppercase[:17])
    df = pd.read_excel(uploaded_file, names=column_names, header=0)
    
    df['CP_Limpio'] = df['O'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df['H'] = df['H'].astype(str).str.strip()
    
    mask_exito = (df['L'].astype(str).str.contains('entregado', case=False, na=False) | 
                  df['L'].astype(str).str.contains('efectividad', case=False, na=False))
    
    # MÉTRICAS GLOBALES
    total_envios = len(df)
    total_exitos = len(df[mask_exito])
    efectividad_global = (total_exitos / total_envios * 100) if total_envios > 0 else 0

    st.markdown('### 📈 Resumen Operativo Global')
    c1, c2, c3 = st.columns(3)
    c1.metric('Total Envíos', f"{total_envios} env.")
    c2.metric('Envíos Entregados', f"{total_exitos} env.")
    c3.metric('Efectividad Global', f"{efectividad_global:.1f}%")
    st.divider()

    tab1, tab2, tab3 = st.tabs(['🚚 Repartidores', '📍 Geografía (CP)', '⚠️ Auditoría de Incidencias'])

    # --- TAB 1: REPARTIDORES ---
    with tab1:
        rep_total = df['H'].value_counts().reset_index()
        rep_total.columns = ['Repartidor', 'Total']
        rep_exitos = df[mask_exito]['H'].value_counts().reset_index()
        rep_exitos.columns = ['Repartidor', 'Exitos']
        resumen_repa = pd.merge(rep_total, rep_exitos, on='Repartidor', how='left').fillna(0)
        resumen_repa['% Efectividad'] = (resumen_repa['Exitos'] / resumen_repa['Total'] * 100).round(1)
        resumen_repa['% Incidencias'] = (100 - resumen_repa['% Efectividad']).round(1)
        
        resumen_filtrado = resumen_repa.sort_values('% Efectividad', ascending=False).head(top_n_repa)
        st.dataframe(resumen_filtrado, use_container_width=True)
        st.bar_chart(resumen_filtrado.set_index('Repartidor')[['Total', 'Exitos']])

    # --- TAB 2: GEOGRAFÍA ---
    with tab2:
        cp_counts = df['CP_Limpio'].value_counts().reset_index()
        cp_counts.columns = ['CP', 'Cantidad']
        cp_counts['Porcentaje'] = (cp_counts['Cantidad'] / total_envios * 100).round(1)
        cp_counts['Etiqueta'] = cp_counts.apply(lambda x: f"{int(x['Cantidad'])} | {x['Porcentaje']}%", axis=1)
        
        fig_cp = px.bar(cp_counts.head(top_n_cp), x='CP', y='Cantidad', text='Etiqueta', color='Cantidad', color_continuous_scale='Blues')
        fig_cp.update_traces(textposition='outside')
        st.plotly_chart(fig_cp, use_container_width=True)

    # --- TAB 3: AUDITORÍA (CON EL TOTALIZADO SOLICITADO) ---
    with tab3:
        st.subheader('🔥 Auditoría General de Incidencias')
        
        # 1. Pivotar motivos de incidencia
        inc_data = df.groupby(['H', 'L']).size().reset_index(name='Cant')
        pivot_inc = inc_data.pivot(index='H', columns='L', values='Cant').fillna(0)
        
        # 2. Calcular el TOTAL de incidencias (sumando las columnas del pivote)
        # Nota: Esto suma todos los motivos que aparecen en la columna 'L'
        pivot_inc['TOTAL_INCIDENCIAS'] = pivot_inc.sum(axis=1)
        
        # 3. Unir con porcentajes generales
        rep_stats = resumen_repa.set_index('Repartidor')[['% Efectividad', '% Incidencias']]
        auditoria_total = rep_stats.merge(pivot_inc, left_index=True, right_index=True, how='left').fillna(0)
        
        # 4. Ordenar de mayor incidencia a menor
        auditoria_total = auditoria_total.sort_values('% Incidencias', ascending=False)

        # 5. Mapa de Calor
        altura = max(8, len(auditoria_total) * 0.4)
        fig_aud, ax_aud = plt.subplots(figsize=(16, altura))
        sns.heatmap(auditoria_total, annot=True, fmt='g', cmap='YlOrRd', ax=ax_aud, linewidths=.5)
        plt.title('Ranking Auditoría: Desglose + Total Incidencias', fontsize=16)
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig_aud)

        # Botón de descarga
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches='tight')
        st.download_button(label="📥 Descargar Auditoría PNG", data=buf.getvalue(), file_name="auditoria_completa.png", mime="image/png")

else:
    st.info('👋 Sube el archivo Excel para procesar los datos.')
