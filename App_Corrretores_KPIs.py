import streamlit as st
import pandas as pd
import psycopg2
import os
import plotly.express as px
import plotly.graph_objects as go
import warnings

from dotenv import load_dotenv

# --- SILENCIAR AVISOS DO PANDAS/STREAMLIT ---
# Isso limpa o log do Render, removendo avisos de depreciação futura
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

# Tenta carregar .env, se não achar, tenta .env.txt
if not load_dotenv():
    load_dotenv('.env.txt') 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="KPIs Araguaia Imóveis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS (IDENTIDADE VISUAL ARAGUAIA) ---
st.markdown("""
    <style>
    .main {
        background-color: #f4f4f9;
    }
    .stApp header {
        background-color: #263318;
    }
    h1, h2, h3 {
        color: #263318;
        font-family: 'Montserrat', sans-serif;
    }
    .metric-card {
        background-color: #ffffff;
        border-left: 5px solid #8cc63f;
        padding: 20px;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background-color: #8cc63f;
        color: #263318;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- LISTA DE CORRETORES (Do Excel) ---
OPCOES_CORRETORES = [
    "4083 - NEURA.T.PAVAN SINIGAGLIA",
    "2796 - PEDRO LAERTE RABECINI",
    "57 - Santos e Padilha Ltda - ME",
    "1376 - VALMIR MARIO TOMASI - SEGALA EMPREENDIMENTOS IMOBILIARIOS EIRELI",
    "1768 - SEGALA EMPREENDIMENTOS IMOBILIARIOS EIRELI",
    "2436 - PAULO EDUARDO GONCALVES DIAS",
    "2447 - GLAUBER BENEDITO FIGUEIREDO DE PINHO",
    "4476 - Priscila Canhet da Silveira",
    "1531 - Walmir de Oliveira Queiroz",
    "4704 - MAYCON JEAN CAMPOS",
    "4084 - JAIMIR COMPAGNONI",
    "4096 - THAYANE APARECIDA BORGES 09648795908",
    "4160 - SIMONE VALQUIRIA BELLO OLIVEIRA",
    "4587 - GABRIEL GALVÃO LOURENÃ‡O EMPREENDIMENTOS LTDA",
    "4802 - CESAR AUGUSTO PORTELA DA FONSECA JUNIOR LTDA",
    "4868 - LENE ENGLER DA SILVA",
    "4087 - JOHNNY MIRANDA OJEDA 47447583120",
    "4531 - MG EMPREENDIMENTOS LTDA (MAIKON WILLIAN CHUSTA)",
    "4587 - GABRIEL GALVAO LOURENÃ‡O EMPREENDIMENTOS LTDA",
    "4826 - JEVIELI BELLO OLIVEIRA",
    "4825 - EVA VITORIA GALVAO LOURENCO",
    "54 - Ronaldo Padilha dos Santos",
    "1137 - Moacir Blemer Olivoto",
    "4872 - WQ CORRETORES LTDA (WALMIR QUEIROZ)",
    "720 - Luciane Bocchi ME",
    "5154 - FELIPE JOSE MOREIRA ALMEIDA",
    "3063 - SILVANA SEGALA",
    "2377 - Paulo Eduardo GonÃ§alves Dias",
    "Outro / Não Listado"
]

# --- CONEXÃO COM O BANCO DE DADOS ---
@st.cache_data(ttl=60) 
def load_data():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    if not DATABASE_URL:
        st.error("⚠️ URL do Banco de Dados não encontrada.")
        return pd.DataFrame()

    try:
        conn = psycopg2.connect(DATABASE_URL)
        # ATUALIZADO: Inclui nota_atendimento
        query = """
        SELECT 
            id, 
            data_hora, 
            nome, 
            nome_corretor, 
            cidade, 
            loteamento, 
            comprou_1o_lote, 
            nivel_interesse,
            foi_atendido,
            nota_atendimento
        FROM atendimentos
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Tratamento de Dados
        df['data_hora'] = pd.to_datetime(df['data_hora'])
        df['nome_corretor'] = df['nome_corretor'].fillna('Não Informado/Orgânico')
        df['loteamento'] = df['loteamento'].fillna('Não Informado')
        df['comprou_1o_lote'] = df['comprou_1o_lote'].fillna('Não')
        df['nivel_interesse'] = df['nivel_interesse'].fillna('Não Classificado')
        
        # Tratamento da Nota: Null vira 0 (Não Avaliado)
        df['nota_atendimento'] = df['nota_atendimento'].fillna(0).astype(int)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# --- CARREGAR DADOS ---
df = load_data()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/263/263115.png", width=50) 
st.sidebar.title("Filtros Araguaia")

if not df.empty:
    # Filtro de Data
    min_date = df['data_hora'].min().date()
    max_date = df['data_hora'].max().date()
    
    start_date, end_date = st.sidebar.date_input("Período", [min_date, max_date])
    
    # Filtro de Empreendimento
    lista_empreendimentos = ['Todos'] + list(df['loteamento'].unique())
    filtro_empreendimento = st.sidebar.selectbox("Empreendimento", lista_empreendimentos)
    
    # Filtro de Corretor
    corretores_no_banco = list(df['nome_corretor'].unique())
    lista_completa_corretores = sorted(list(set(OPCOES_CORRETORES + corretores_no_banco)))
    lista_filtro = ['Todos'] + lista_completa_corretores
    
    filtro_corretor = st.sidebar.selectbox("Corretor", lista_filtro)

    # APLICAR FILTROS
    df_filtered = df[
        (df['data_hora'].dt.date >= start_date) & 
        (df['data_hora'].dt.date <= end_date)
    ]
    
    if filtro_empreendimento != 'Todos':
        df_filtered = df_filtered[df_filtered['loteamento'] == filtro_empreendimento]
        
    if filtro_corretor != 'Todos':
        df_filtered = df_filtered[df_filtered['nome_corretor'] == filtro_corretor]

else:
    st.info("Aguardando dados no banco...")
    df_filtered = df

# --- TÍTULO PRINCIPAL ---
st.title("📊 Dashboard de Performance - Araguaia Imóveis")
st.markdown("---")

if not df_filtered.empty:
    
    # --- CÁLCULO DE KPIS GERAIS ---
    total_atendimentos = len(df_filtered)
    conversoes = len(df_filtered[df_filtered['comprou_1o_lote'] == 'Sim'])
    taxa_conversao = (conversoes / total_atendimentos * 100) if total_atendimentos > 0 else 0
    interesse_alto = len(df_filtered[df_filtered['nivel_interesse'] == 'Alto'])
    taxa_interesse_alto = (interesse_alto / total_atendimentos * 100) if total_atendimentos > 0 else 0
    
    # --- CÁLCULO DE AVALIAÇÕES (NOVO - ESCALA 1 a 5) ---
    df_avaliados = df_filtered[df_filtered['nota_atendimento'] > 0]
    qtd_avaliacoes = len(df_avaliados)
    
    if qtd_avaliacoes > 0:
        media_geral_nota = df_avaliados['nota_atendimento'].mean()
    else:
        media_geral_nota = 0

    # --- LINHA DE MÉTRICAS (5 COLUNAS) ---
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Atendimentos", total_atendimentos)
    with col2:
        st.metric("Vendas (1º Lote)", f"{conversoes}", delta=f"{taxa_conversao:.1f}% Conv.")
    with col3:
        st.metric("Interesse Alto", interesse_alto, delta=f"{taxa_interesse_alto:.1f}% do total")
    with col4:
        # Métrica de Qualidade
        st.metric("⭐ Nota Média (1-5)", f"{media_geral_nota:.2f}", delta=f"{qtd_avaliacoes} avaliações")
    with col5:
        top_corretor = df_filtered['nome_corretor'].mode()[0] if not df_filtered.empty else "-"
        st.metric("Top Volumetria", top_corretor)

    st.markdown("---")

    # --- GRÁFICOS LINHA 1 ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🏘️ Volume por Empreendimento")
        vol_emp = df_filtered['loteamento'].value_counts().reset_index()
        vol_emp.columns = ['Empreendimento', 'Volume']
        fig_emp = px.bar(vol_emp, x='Empreendimento', y='Volume', color_discrete_sequence=['#263318'], text='Volume')
        st.plotly_chart(fig_emp, width="stretch") # CORRIGIDO width

    with c2:
        st.subheader("💰 Funil de Conversão")
        cross_tab = pd.crosstab(df_filtered['nivel_interesse'], df_filtered['comprou_1o_lote']).reset_index()
        cross_tab_melt = cross_tab.melt(id_vars='nivel_interesse', var_name='Comprou', value_name='Qtd')
        fig_bar_stack = px.bar(cross_tab_melt, x="nivel_interesse", y="Qtd", color="Comprou", 
                               color_discrete_map={'Sim': '#8cc63f', 'Não': '#263318'}, barmode='group')
        st.plotly_chart(fig_bar_stack, width="stretch") # CORRIGIDO width

    # --- GRÁFICOS LINHA 2: QUALIDADE (ESCALA 1-5) ---
    st.markdown("### ⭐ Qualidade do Atendimento")
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("🏆 Ranking de Nota Média")
        if not df_avaliados.empty:
            ranking = df_avaliados.groupby('nome_corretor')['nota_atendimento'].agg(['mean', 'count']).reset_index()
            # Filtra apenas quem tem avaliações
            ranking = ranking[ranking['count'] > 0].sort_values(by='mean', ascending=False).head(10)
            
            fig_qualidade = px.bar(
                ranking, 
                x='mean', 
                y='nome_corretor', 
                orientation='h',
                text_auto='.2f',
                color='mean',
                color_continuous_scale=['#d9534f', '#f0ad4e', '#8cc63f'],
                range_color=[1, 5], # TRAVA A ESCALA DE COR EM 5
                labels={'mean': 'Média (1-5)', 'nome_corretor': 'Corretor'}
            )
            # Ajuste visual do eixo X para não cortar em 5 exato
            fig_qualidade.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Nota Média (1 a 5)", xaxis=dict(range=[0, 5.5]))
            st.plotly_chart(fig_qualidade, width="stretch")
        else:
            st.info("Ainda não há avaliações suficientes.")

    with c4:
        st.subheader("📊 Distribuição das Notas")
        if not df_avaliados.empty:
            # AJUSTE PARA ESCALA 1-5 (nbins=5 e eixo X linear)
            fig_hist = px.histogram(
                df_avaliados, 
                x="nota_atendimento", 
                nbins=5, 
                color_discrete_sequence=['#8cc63f'],
                text_auto=True
            )
            fig_hist.update_layout(
                bargap=0.2, 
                xaxis_title="Nota (1 a 5)", 
                yaxis_title="Quantidade",
                xaxis=dict(tickmode='linear', dtick=1) # FORÇA NÚMEROS INTEIROS NO EIXO X
            )
            st.plotly_chart(fig_hist, width="stretch")
        else:
            st.info("Sem dados de avaliações no período.")

    # --- GRÁFICOS LINHA 3: VOLUMETRIA ---
    st.markdown("### 🧑‍💼 Produtividade (Volume)")
    vol_corr = df_filtered['nome_corretor'].value_counts().reset_index().head(15)
    vol_corr.columns = ['Corretor', 'Volume']
    fig_corr = px.bar(vol_corr, x='Volume', y='Corretor', orientation='h', color_discrete_sequence=['#263318'], text='Volume')
    fig_corr.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
    st.plotly_chart(fig_corr, width="stretch") # CORRIGIDO width

    # --- DADOS BRUTOS ---
    with st.expander("📋 Ver Dados Detalhados (Com Notas)"):
        colunas_ordem = ['data_hora', 'nome_corretor', 'nome', 'nota_atendimento', 'nivel_interesse', 'comprou_1o_lote', 'loteamento']
        # Tenta exibir ordenado, se as colunas existirem
        cols_existentes = [c for c in colunas_ordem if c in df_filtered.columns]
        st.dataframe(df_filtered[cols_existentes].sort_values(by='data_hora', ascending=False))
        
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar CSV Completo", csv, "kpis_araguaia_v2.csv", "text/csv")

else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
