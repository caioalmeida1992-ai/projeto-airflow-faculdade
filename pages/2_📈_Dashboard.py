import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
from google.cloud import storage
import json

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard de Recomendações", layout="wide")
st.title("📈 Dashboard de Análise e Recomendações")

# --- Conexão Segura com o MongoDB Atlas ---
@st.cache_data
def load_data_from_mongo():
    """Conecta no MongoDB e carrega os dados da coleção 'viagens'."""
    try:
        # Pega a string de conexão dos "Secrets" (que estarão no arquivo mongo_uri.txt na VM)
        with open("mongo_uri.txt", "r") as f:
            mongo_conn_string = f.read().strip()
        
        client = MongoClient(mongo_conn_string, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client["empresa_onibus"]
        collection = db["viagens"]
        data = list(collection.find())

        if data:
            for item in data:
                item["_id"] = str(item["_id"])
        client.close()

        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao conectar com o MongoDB: {e}. Verifique o arquivo mongo_uri.txt na VM.")
        return pd.DataFrame()

# --- (O restante do seu código de lógica e visualização continua exatamente o mesmo) ---

# --- Lógica de Recomendação ---
def get_recommendations(df_cliente, all_destinations):
    destinos_excluidos = df_cliente[df_cliente['nota_destino'] < 3]['destino'].tolist()
    destinos_favoritos = df_cliente[df_cliente['nota_destino'] >= 4]['destino'].tolist()
    if not destinos_favoritos: return ["Avalie mais viagens positivamente para receber recomendações!"]
    similar_destinations = {"Salvador, BA": ["Recife, PE", "Fortaleza, CE"], "São Paulo, SP": ["Curitiba, PR", "Belo Horizonte, MG"], "Rio de Janeiro, RJ": ["Florianópolis, SC", "Búzios, RJ"], "Gramado, RS": ["Canela, RS", "Campos do Jordão, SP"]}
    recomendacoes = set()
    for destino in destinos_favoritos:
        if destino in similar_destinations: recomendacoes.update(similar_destinations[destino])
    recomendacoes_finais = [rec for rec in recomendacoes if rec not in df_cliente['destino'].tolist() and rec not in destinos_excluidos]
    return recomendacoes_finais if recomendacoes_finais else ["Já recomendamos todos os destinos similares aos seus favoritos!"]

# --- Lógica de Previsão de Férias ---
def predict_vacation_month(df_cliente):
    df_ferias = df_cliente[df_cliente['periodo_ferias'] == True]
    if df_ferias.empty: return "Ainda não temos dados suficientes para prever seu período de férias."
    df_ferias['data_inicio'] = pd.to_datetime(df_ferias['data_inicio'])
    try: mes_mais_comum = df_ferias['data_inicio'].dt.month_name(locale='pt_BR.utf8').mode()
    except Exception: mes_mais_comum = df_ferias['data_inicio'].dt.month_name().mode()
    return f"Percebemos um padrão de viagens longas no mês de **{mes_mais_comum[0]}**. Uma boa época para enviar ofertas!" if not mes_mais_comum.empty else "Não foi possível identificar um padrão de férias."

# --- Carregando os Dados ---
df = load_data_from_mongo()
st.sidebar.header("Filtros e Ações")
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

if df.empty:
    st.warning("Ainda não há dados de viagens no banco de dados. Envie algumas avaliações e aguarde o processamento do pipeline.")
else:
    clientes = sorted(df['id_cliente'].unique())
    cliente_selecionado = st.sidebar.selectbox("Selecione um Cliente", clientes)
    df_cliente = df[df['id_cliente'] == cliente_selecionado]
    st.header(f"Análise para o cliente: {cliente_selecionado}")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💡 Recomendações para Próximas Viagens")
        recomendacoes = get_recommendations(df_cliente, df['destino'].unique())
        for rec in recomendacoes: st.success(rec)
    with col2:
        st.subheader("🗓️ Previsão de Férias")
        previsao = predict_vacation_month(df_cliente)
        st.info(previsao)
    st.markdown("---")
    st.subheader("📊 Histórico de Avaliações")
    fig = px.bar(df_cliente, x='destino', y='nota_destino', title='Notas dadas aos destinos visitados', labels={'destino': 'Destino', 'nota_destino': 'Nota (0-5)'}, color='nota_destino', color_continuous_scale=px.colors.sequential.Viridis)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("📜 Histórico Detalhado de Viagens")
    st.dataframe(df_cliente, use_container_width=True)
