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

# Este filtro solo se aplicará al Tab 1
top_n_repa = st.sidebar.slider('Repartidores a mostrar en Tab 1', min_value=5, max_value=30, value=10)

if uploaded_file is not None:
    # 1. Preparación de datos
    column_names = list(string.ascii_uppercase[:17])
    df = pd.read_excel(uploaded_file, names=column_names, header=0)
    
    # Limpieza de CP y Repartidores
    df['CP_Limpio'] = df['O'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df['H'] = df['H'].astype(str).str.strip()
    
    # Filtro de éxito
    mask_exito = (df['L'].astype(str).str.contains('entregado', case=False, na=False) | 
                  df['L'].astype(str).str.contains('efectividad', case=False, na=False))
    
    # --- MÉTRICAS GLOBALES ---
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

    tab1, tab2, tab3 = st.tabs(['🚚 Repartidores', '📍 Geografía (CP)', '⚠️ Auditoría de Incidencias'])

    # --- TAB 1: REPARTIDORES (CON FILTRO) ---
    with tab1:
        st.subheader(f'Rendimiento: Top {top_n_repa} Repartidores')
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

    # --- TAB 2: GEOGRAFÍA (TODOS LOS CP CON DOBLE ETIQUETA) ---
    with tab2:
        st.subheader('📍 Distribución Completa por Código Postal')
        cp_counts = df['CP_Limpio'].value_counts().reset_index()
        cp_counts.columns = ['CP', 'Cantidad']
        
        # Calcular Porcentaje
        cp_counts['Porcentaje'] = (cp_counts['Cantidad'] / total_envios * 100).round(1)
        
        # Crear la etiqueta combinada: "Valor | %"
        cp_counts['Etiqueta'] = cp_counts.apply(lambda x: f"{int(x['Cantidad'])} | {x['Porcentaje']}%", axis=1)
        
        # Gráfico con TODOS los CP y etiquetas personalizadas
        fig_cp = px.bar(
            cp_counts, 
            x='CP', 
            y='Cantidad',
            text='Etiqueta', # Usamos la nueva columna combinada
            color='Cantidad', 
            color_continuous_scale='Blues',
            labels={'CP': 'Código Postal', 'Cantidad': 'Nº Envíos'}
        )
        
        # Ajustes visuales para que las etiquetas se lean bien
        fig_cp.update_traces(textposition='outside', textfont_size=12)
        fig_cp.update_layout(
            xaxis_type='category',
            uniformtext_minsize=8, 
            uniformtext_mode='hide',
            height=600
        )
        
        st.plotly_chart(fig_cp, use_container_width=True)
        st.info(f"Se están analizando {len(cp_counts)} códigos postales diferentes.")

    # --- TAB 3: AUDITORÍA (IGUAL QUE ANTES) ---
    with tab3:
        st.subheader('🔥 Auditoría General de Incidencias')
        inc_data = df.groupby(['H', 'L']).size().reset_index(name='Cant')
        pivot_inc = inc_data.pivot(index='H', columns='L', values='Cant').fillna(0)
        rep_stats_all = resumen_repa.set_index('Repartidor')[['% Efectividad', '% Incidencias']]
        auditoria_total = rep_stats_all.merge(pivot_inc, left_index=True, right_index=True, how='left').fillna(0)
        auditoria_total = auditoria_total.sort_values('% Incidencias', ascending=False)

        altura_dinamica = max(8, len(auditoria_total) * 0.4)
        fig_aud, ax_aud = plt.subplots(figsize=(14, altura_dinamica))
        sns.heatmap(auditoria_total, annot=True, fmt='g', cmap='YlOrRd', ax=ax_aud, linewidths=.5)
        plt.title('Ranking de Incidencias por Repartidor', fontsize=16)
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig_aud)

else:
    st.info('👋 Por favor, sube el archivo Excel para procesar los datos.')

