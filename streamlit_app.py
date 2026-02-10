import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import string

st.set_page_config(page_title='Dashboard Logístico', layout='wide')
st.title('📊 Análisis Avanzado de Repartos')

# Sidebar para carga de archivo
st.sidebar.header('Configuración')
uploaded_file = st.sidebar.file_uploader('Cargar archivo Excel (detalle_envio.xlsx)', type=['xlsx'])

if uploaded_file is not None:
    # 1. CARGA Y PREPARACIÓN
    column_names = list(string.ascii_uppercase[:17])
    df = pd.read_excel(uploaded_file, names=column_names, header=0)
    df['CP_Limpio'] = df['O'].astype(str).str.replace('.0', '', regex=False)
    
    # Métricas Principales
    st.markdown('### 📈 Métricas Clave')
    col1, col2, col3 = st.columns(3)
    col1.metric('Total Envíos', len(df))
    col2.metric('CPs Únicos', df['CP_Limpio'].nunique())
    col3.metric('Repartidores', df['H'].nunique())

    tab1, tab2, tab3, tab4 = st.tabs(['🚚 Repartidores', '📍 Geografía', '⚠️ Incidencias', '🏠 Micro-Hubs'])

    with tab1:
        st.subheader('Rendimiento por Repartidor')
        effective_filter = 'Causa Ajena'
        df_eff = df[df['L'] == effective_filter]
        rep_counts = df_eff['H'].value_counts().reset_index(name='Entregado,Efectividad')
        rep_counts.columns = ['Repartidor', 'Frecuencia']
        
        st.write('Top 5 Repartidores con Mayores Entregas')
        st.dataframe(rep_counts.head(5))
        
        fig, ax = plt.subplots()
        sns.barplot(data=rep_counts.head(5), x='Frecuencia', y='Repartidor', ax=ax, palette='viridis')
        st.pyplot(fig)

    with tab2:
        st.subheader('Distribución por Código Postal')
        cp_dens = df['CP_Limpio'].value_counts().reset_index(name='Densidad')
        cp_dens.columns = ['CP', 'Densidad']
        st.bar_chart(cp_dens.head(15).set_index('CP'))

    with tab3:
        st.subheader('Mapa de Calor de Incidencias')
        inc_data = df.groupby(['H', 'L']).size().reset_index(name='Count')
        top_reps = inc_data.groupby('H')['Count'].sum().nlargest(15).index
        pivot_inc = inc_data[inc_data['H'].isin(top_reps)].pivot(index='H', columns='L', values='Count').fillna(0)
        
        fig_heat, ax_heat = plt.subplots(figsize=(10, 8))
        sns.heatmap(pivot_inc, annot=True, fmt='g', cmap='YlGnBu', ax=ax_heat)
        st.pyplot(fig_heat)

    with tab4:
        st.subheader('Propuesta de Micro-Hubs')
        hub_data = cp_dens.head(15).copy()
        hub_data['Prefijo'] = hub_data['CP'].str[:3]
        micro_hubs = hub_data.loc[hub_data.groupby('Prefijo')['Densidad'].idxmax()]
        st.table(micro_hubs)

else:
    st.info('Por favor, sube el archivo Excel en la barra lateral para comenzar el análisis.')
