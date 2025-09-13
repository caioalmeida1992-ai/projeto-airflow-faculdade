import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

st.set_page_config(page_title="Dashboard de Recomendações", layout="wide")
st.title("📈 Dashboard de Análise e Recomendações")

# Conexão com o MongoDB
@st.cache_data
def load_data_from_mongo():
    try:
        ip_do_windows_wsl = "172.23.0.1"
        client = MongoClient(f"mongodb://{ip_do_windows_wsl}:27017/", serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client["empresa_onibus"]
        collection = db["viagens"]

        data = list(collection.find())

        if data:
            for item in data:
                item["_id"] = str(item["_id"])

        client.close()

        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao conectar com o MongoDB: {e}")
        return pd.DataFrame()


# Lógica de Recomendação
def get_recommendations(df_cliente, all_destinations):
    """Gera recomendações baseadas no histórico do cliente."""
    destinos_excluidos = df_cliente[df_cliente['nota_destino'] < 3]['destino'].tolist()
    destinos_favoritos = df_cliente[df_cliente['nota_destino'] >= 4]['destino'].tolist()

    if not destinos_favoritos:
        return ["Avalie mais viagens positivamente para receber recomendações!"]

    # mockei alguns destinos, mas o ideal para um projeto real, seria consumir de um outro banco de destinos
    similar_destinations = {
        "Salvador, BA": ["Recife, PE", "Fortaleza, CE", "Maceió, AL"],
        "São Paulo, SP": ["Curitiba, PR", "Belo Horizonte, MG"],
        "Rio de Janeiro, RJ": ["Florianópolis, SC", "Búzios, RJ"],
        "Gramado, RS": ["Canela, RS", "Campos do Jordão, SP"]
    }

    recomendacoes = set()
    for destino in destinos_favoritos:
        if destino in similar_destinations:
            recomendacoes.update(similar_destinations[destino])

    recomendacoes_finais = [
        rec for rec in recomendacoes if rec not in df_cliente['destino'].tolist() and rec not in destinos_excluidos
    ]

    if not recomendacoes_finais:
        return ["Já recomendamos todos os destinos similares aos seus favoritos! Explore novos lugares!"]

    return recomendacoes_finais


# --- Lógica de Previsão de Férias ---
def predict_vacation_month(df_cliente):
    """Prevê o provável mês de férias do cliente."""
    df_ferias = df_cliente[df_cliente['periodo_ferias'] == True]

    if df_ferias.empty:
        return "Ainda não temos dados suficientes para prever seu período de férias."

    df_ferias['data_inicio'] = pd.to_datetime(df_ferias['data_inicio'])

    try:
        mes_mais_comum = df_ferias['data_inicio'].dt.month_name(locale='pt_BR.utf8').mode()
    except Exception:
        mes_mais_comum = df_ferias['data_inicio'].dt.month_name().mode()  # Fallback sem locale

    if not mes_mais_comum.empty:
        return f"Percebemos um padrão de viagens longas no mês de **{mes_mais_comum[0]}**. Uma boa época para enviar ofertas!"
    else:
        return "Não foi possível identificar um padrão de férias."


# Carregando os dados do mongo
df = load_data_from_mongo()

# Aqui inicia uma parte mais front do streamlit, criando botões eetc
# Barra Lateral para Filtros e Ações
st.sidebar.header("Filtros e Ações")

if st.sidebar.button("🔄 Atualizar Dados"):
    # ⭐ NOVA LINHA: Limpa o cache da função que busca os dados
    st.cache_data.clear()
    st.rerun()  # Recarrega a página para refletir a mudança

if df.empty:
    st.warning("Ainda não há dados de viagens no banco de dados. Envie algumas avaliações pelo App de Coleta.")
else:
    clientes = sorted(df['id_cliente'].unique())
    cliente_selecionado = st.sidebar.selectbox("Selecione um Cliente", clientes)

    df_cliente = df[df['id_cliente'] == cliente_selecionado]

    st.header(f"Análise para o cliente: {cliente_selecionado}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💡 Recomendações para Próximas Viagens")
        recomendacoes = get_recommendations(df_cliente, df['destino'].unique())
        for rec in recomendacoes:
            st.success(rec)

    with col2:
        st.subheader("🗓️ Previsão de Férias")
        previsao = predict_vacation_month(df_cliente)
        st.info(previsao)

    st.markdown("---")

    st.subheader("📊 Histórico de Avaliações")

    fig = px.bar(df_cliente,
                 x='destino',
                 y='nota_destino',
                 title='Notas dadas aos destinos visitados',
                 labels={'destino': 'Destino', 'nota_destino': 'Nota (0-5)'},
                 color='nota_destino',
                 color_continuous_scale=px.colors.sequential.Viridis)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📜 Histórico Detalhado de Viagens")
    st.dataframe(df_cliente, use_container_width=True)