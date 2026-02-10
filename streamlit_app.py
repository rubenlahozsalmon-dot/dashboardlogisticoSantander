import streamlit as st
import pandas as pd
import string
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title='Dashboard Logístico', layout='wide')
st.title('📊 Dashboard de Auditoría Logística')

# --- CARGA DE ARCHIVO ---
st.sidebar.header('Configuración')
uploaded_file = st.sidebar.file_uploader('Cargar archivo Excel (detalle_envio.xlsx)', type=['xlsx'])

if uploaded_file is not None:
    # 1. Preparación de datos
    column_names = list(string.ascii_uppercase[:17])
    df = pd.read_excel(uploaded_file, names=column_names, header=0)
    df['CP_Limpio'] = df['O'].astype(str).str.replace('.0', '', regex=False)
    
    # Filtro flexible de éxito
    mask_exito = (df['L'].astype(str).str.contains('entregado', case=False, na=False) | 
                  df['L'].astype(str).str.contains('efectividad', case=False, na=False))
    
    # --- MÉTRICAS GLOBALES ---
    total_envios = len(df)
    total_exitos = len(df[mask_exito])
    efectividad_global = (total_exitos / total_envios * 100) if total_envios > 0 else 0

    st.markdown('### 📈 Resumen Operativo Global')
    c1, c2, c3 = st.columns(3)
    c1.metric('Total Envíos', f"{total_envios} paq.")
    c2.metric('Entregas Exitosas', f"{total_exitos} paq.")
    c3.metric('Efectividad Global', f"{efectividad_global:.1f}%")
    st.progress(efectividad_global / 100)
    st.divider()

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(['🚚 Repartidores', '📍 Geografía (CP)', '⚠️ Incidencias'])

    with tab1:
        st.subheader('Rendimiento por Repartidor')
        rep_total = df['H'].value_counts().reset_index(name='Total')
        rep_exitos = df[mask_exito]['H'].value_counts().reset_index(name='Exitos')
        resumen_repa = pd.merge(rep_total, rep_exitos, on='index', how='left').fillna(0)
        resumen_repa.columns = ['Repartidor', 'Total', 'Exitos']
        resumen_repa['% Efectividad'] = (resumen_repa['Exitos'] / resumen_repa['Total'] * 100).round(1)
        
        st.dataframe(resumen_repa.sort_values('% Efectividad', ascending=False), use_container_width=True)
        st.bar_chart(resumen_repa.head(10).set_index('Repartidor')[['Total', 'Exitos']])

    with tab2:
        st.subheader('Distribución por Código Postal')
        cp_counts = df['CP_Limpio'].value_counts().reset_index()
        cp_counts.columns = ['CP', 'Cantidad']
        cp_counts['Porcentaje'] = (cp_counts['Cantidad'] / total_envios * 100).round(1)
        
        # Gráfico con porcentajes sobre las barras
        fig_cp = px.bar(cp_counts.head(15), x='CP', y='Cantidad',
                        text=cp_counts.head(15)['Porcentaje'].apply(lambda x: f'{x}%'),
                        color='Cantidad', color_continuous_scale='Blues',
                        labels={'CP': 'Código Postal', 'Cantidad': 'Envíos'})
        fig_cp.update_traces(textposition='outside')
        fig_cp.update_layout(xaxis_type='category')
        st.plotly_chart(fig_cp, use_container_width=True)

    with tab3:
        st.subheader('🔥 Mapa de Calor de Incidencias')
        
        # Procesar tabla pivote
        inc_data = df.groupby(['H', 'L']).size().reset_index(name='Count')
        pivot_inc = inc_data.pivot(index='H', columns='L', values='Count').fillna(0)
        
        # Calcular efectividad individual para la primera columna
        rep_efectividad = resumen_repa.set_index('Repartidor')['% Efectividad']
        
        # Ordenar columnas de incidencias por volumen
        col_order = pivot_inc.sum(axis=0).sort_values(ascending=False).index
        pivot_inc = pivot_inc[col_order]
        
        # Insertar Efectividad a la izquierda
        pivot_inc.insert(0, 'EFECTIVIDAD (%)', rep_efectividad)
        
        # Ordenar filas por volumen total de incidencias
        pivot_inc['Total_Inc'] = pivot_inc.iloc[:, 1:].sum(axis=1)
        pivot_inc = pivot_inc.sort_values('Total_Inc', ascending=False).drop(columns='Total_Inc')

        # Dibujar Mapa de Calor
        fig_heat, ax_heat = plt.subplots(figsize=(12, 8))
        sns.heatmap(pivot_inc.head(20), annot=True, fmt='g', cmap='YlOrRd', ax=ax_heat, linewidths=.5)
        plt.title('Top 20 Repartidores: Efectividad vs Incidencias')
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig_heat)

        # Botón de Descarga
        buf = io.BytesIO()
        fig_heat.savefig(buf, format="png", bbox_inches='tight')
        st.download_button(label="📥 Descargar Mapa de Calor (PNG)", 
                           data=buf.getvalue(), 
                           file_name="incidencias.png", 
                           mime="image/png")

else:
    st.info('👋 Por favor, sube el archivo Excel en la barra lateral para generar el reporte.')

