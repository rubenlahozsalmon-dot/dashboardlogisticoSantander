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

# --- CARGA DE ARCHIVO Y FILTROS ---
st.sidebar.header('Configuración')
uploaded_file = st.sidebar.file_uploader('Cargar archivo Excel', type=['xlsx'])
top_n = st.sidebar.slider('Cantidad de repartidores a mostrar', min_value=5, max_value=30, value=15)

if uploaded_file is not None:
    column_names = list(string.ascii_uppercase[:17])
    df = pd.read_excel(uploaded_file, names=column_names, header=0)
    df['CP_Limpio'] = df['O'].astype(str).str.replace('.0', '', regex=False).str.strip()
    
    mask_exito = (df['L'].astype(str).str.contains('entregado', case=False, na=False) | 
                  df['L'].astype(str).str.contains('efectividad', case=False, na=False))
    
    # MÉTRICAS GLOBALES
    total_envios = len(df)
    total_exitos = len(df[mask_exito])
    efectividad_global = (total_exitos / total_envios * 100) if total_envios > 0 else 0

    st.markdown(f'### 📈 Resumen Operativo ({total_envios} envíos)')
    c1, c2, c3 = st.columns(3)
    c1.metric('Total Envíos', f"{total_envios} env.")
    c2.metric('Entregados', f"{total_exitos} env.")
    c3.metric('Efectividad', f"{efectividad_global:.1f}%")
    st.divider()

    tab1, tab2, tab3 = st.tabs(['🚚 Repartidores', '📍 Geografía (CP)', '⚠️ Mapa de Calor'])

    with tab1:
        rep_total = df['H'].value_counts().reset_index()
        rep_total.columns = ['Repartidor', 'Total']
        rep_exitos = df[mask_exito]['H'].value_counts().reset_index()
        rep_exitos.columns = ['Repartidor', 'Exitos']
        resumen_repa = pd.merge(rep_total, rep_exitos, on='Repartidor', how='left').fillna(0)
        resumen_repa['% Efectividad'] = (resumen_repa['Exitos'] / resumen_repa['Total'] * 100).round(1)
        resumen_repa['% Incidencias'] = (100 - resumen_repa['% Efectividad']).round(1)
        st.dataframe(resumen_repa.sort_values('% Efectividad', ascending=False), use_container_width=True)

    with tab2:
        cp_df = df['CP_Limpio'].value_counts().reset_index()
        cp_df.columns = ['CP', 'Cantidad']
        cp_df['Porcentaje'] = (cp_df['Cantidad'] / total_envios * 100).round(1)
        fig_cp = px.bar(cp_df.head(top_n), x='CP', y='Cantidad',
                        text=cp_df.head(top_n)['Porcentaje'].apply(lambda x: f'{x}%'),
                        color='Cantidad', color_continuous_scale='Blues')
        fig_cp.update_traces(textposition='outside')
        st.plotly_chart(fig_cp, use_container_width=True)

    with tab3:
        st.subheader(f'🔥 Auditoría de Incidencias (Top {top_n} Repartidores)')
        
        # Procesar incidencias
        inc_data = df.groupby(['H', 'L']).size().reset_index(name='Count')
        pivot_inc = inc_data.pivot(index='H', columns='L', values='Count').fillna(0)
        
        # Identificar columna de éxito
        col_exito = next((c for c in pivot_inc.columns if "entregado" in str(c).lower() or "efectividad" in str(c).lower()), None)
        
        # Unir con porcentajes
        rep_stats = resumen_repa.set_index('Repartidor')[['% Efectividad', '% Incidencias']]
        full_pivot = pivot_inc.merge(rep_stats, left_index=True, right_index=True, how='left').fillna(0)
        
        # Columnas para el gráfico
        cols_verdes = ['% Efectividad'] + ([col_exito] if col_exito else [])
        cols_rojas = ['% Incidencias'] + [c for c in pivot_inc.columns if c != col_exito]
        
        # Ordenar a los repartidores de PEOR a MEJOR (los peores arriba para que llamen la atención)
        full_pivot['Total_Inc_Ranking'] = full_pivot[['% Incidencias']].copy()
        ranking_df = full_pivot.sort_values('% Incidencias', ascending=False).head(top_n)
        
        # Crear Gráfico Único Grande
        fig_final, ax_final = plt.subplots(figsize=(14, 0.8 * top_n)) # Tamaño dinámico según el Top seleccionado
        
        # Capa de Incidencias (Rojo)
        sns.heatmap(ranking_df[cols_rojas], annot=True, fmt='g', cmap='YlOrRd', ax=ax_final, cbar=False, linewidths=.5)
        # Capa de Éxito (Verde) - Se dibuja solo en sus columnas correspondientes
        sns.heatmap(ranking_df[cols_verdes], annot=True, fmt='g', cmap='Greens', ax=ax_final, cbar=False, linewidths=.5)
        
        plt.title(f"Ranking de Desempeño: Los {top_n} con más Incidencias", fontsize=16)
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig_final)
        
        # Botón de descarga
        buf = io.BytesIO()
        fig_final.savefig(buf, format="png", bbox_inches='tight')
        st.download_button(label="📥 Descargar Mapa de Calor Completo", data=buf.getvalue(), file_name="auditoria_completa.png", mime="image/png")

else:
    st.info('👋 Sube el archivo Excel para activar la auditoría.')

