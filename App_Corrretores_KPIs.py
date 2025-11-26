import streamlit as st
import pandas as pd
import psycopg2
import os
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

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
        width: 100%;
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
# Alterado TTL para 15 segundos para atualizar mais rápido automaticamente
@st.cache_data(ttl=15) 
def load_data():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    if not DATABASE_URL:
        st.error("⚠️ URL do Banco de Dados não encontrada.")
        return pd.DataFrame()

    try:
        conn = psycopg2.connect(DATABASE_URL)
        # --- ATUALIZAÇÃO: Adicionado nota_atendimento na query ---
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
        
        # --- NOVO: Tratamento da nota ---
        # Converte para numérico e preenche vazios com 0
        df['nota_atendimento'] = pd.to_numeric(df['nota_atendimento'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# --- BARRA LATERAL (FILTROS E UPDATE) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/263/263115.png", width=50)
st.sidebar.title("Filtros Araguaia")

# --- NOVO: BOTÃO DE ATUALIZAÇÃO MANUAL ---
if st.sidebar.button("🔄 Atualizar Dados Agora"):
    st.cache_data.clear()
    st.rerun()

# Carrega os dados
df = load_data()

if not df.empty:
    # Filtro de Data
    min_date = df['data_hora'].min().date()
    max_date = df['data_hora'].max().date()
    
    start_date, end_date = st.sidebar.date_input(
        "Período",
        [min_date, max_date]
    )
    
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
    
    # Cálculo da Média de Notas (Considerando apenas quem deu nota > 0)
    avaliacoes_validas = df_filtered[df_filtered['nota_atendimento'] > 0]
    media_nota = avaliacoes_validas['nota_atendimento'].mean() if not avaliacoes_validas.empty else 0
    qtd_avaliacoes = len(avaliacoes_validas)

    # --- LINHA DE MÉTRICAS (Agora com 5 colunas para caber a Nota) ---
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total de Atendimentos", total_atendimentos)
    with col2:
        st.metric("Realizaram Sonho", f"{conversoes}", delta=f"{taxa_conversao:.1f}%")
    with col3:
        st.metric("Interesse Alto", interesse_alto, delta=f"{taxa_interesse_alto:.1f}%")
    with col4:
        # Mostra a média e a quantidade de votos
        st.metric("Média Avaliação (1-5)", f"{media_nota:.1f} ⭐", f"{qtd_avaliacoes} votos")
    with col5:
        top_corretor = df_filtered['nome_corretor'].mode()[0] if not df_filtered.empty else "-"
        st.metric("Corretor Destaque", top_corretor)

    st.markdown("---")

    # --- GRÁFICOS LINHA 1 ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🏘️ Por Empreendimento")
        vol_emp = df_filtered['loteamento'].value_counts().reset_index()
        vol_emp.columns = ['Empreendimento', 'Volume']
        fig_emp = px.bar(vol_emp, x='Empreendimento', y='Volume', color_discrete_sequence=['#263318'], text='Volume')
        st.plotly_chart(fig_emp, use_container_width=True)

    with c2:
        st.subheader("🧑‍💼 Por Corretor")
        vol_corr = df_filtered['nome_corretor'].value_counts().reset_index().head(10)
        vol_corr.columns = ['Corretor', 'Volume']
        fig_corr = px.bar(vol_corr, x='Volume', y='Corretor', orientation='h', color_discrete_sequence=['#8cc63f'], text='Volume')
        fig_corr.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_corr, use_container_width=True)

    # --- GRÁFICOS LINHA 2 ---
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("🔥 Nível de Interesse")
        fig_pie = px.pie(df_filtered, names='nivel_interesse', hole=0.4, color_discrete_sequence=['#8cc63f', '#263318', '#4a5e35'])
        st.plotly_chart(fig_pie, use_container_width=True)

    with c4:
        st.subheader("💰 Conversão por Interesse")
        # Gráfico empilhado
        cross_tab = pd.crosstab(df_filtered['nivel_interesse'], df_filtered['comprou_1o_lote']).reset_index()
        cross_tab_melt = cross_tab.melt(id_vars='nivel_interesse', var_name='Comprou', value_name='Qtd')
        fig_bar_stack = px.bar(cross_tab_melt, x="nivel_interesse", y="Qtd", color="Comprou", 
                               color_discrete_map={'Sim': '#8cc63f', 'Não': '#263318'}, barmode='group')
        st.plotly_chart(fig_bar_stack, use_container_width=True)

    # --- DADOS BRUTOS ---
    with st.expander("📋 Ver Dados Brutos (Incluindo Notas)"):
        # Mostrando colunas principais primeiro
        cols_order = ['id', 'data_hora', 'nome', 'nota_atendimento', 'nome_corretor', 'loteamento', 'comprou_1o_lote']
        # Pega apenas as colunas que existem no df (para evitar erro se mudar algo no futuro)
        cols_to_show = [c for c in cols_order if c in df_filtered.columns] + [c for c in df_filtered.columns if c not in cols_order]
        
        st.dataframe(df_filtered[cols_to_show].sort_values(by='data_hora', ascending=False))
        
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar CSV", csv, "kpis_araguaia.csv", "text/csv")

else:
    st.warning("Nenhum dado encontrado.")
