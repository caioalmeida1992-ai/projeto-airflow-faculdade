# Conteúdo ATUALIZADO para: app_coleta.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from google.cloud import storage
import json

# --- Configuração da Página ---
st.set_page_config(page_title="Coleta de Avaliação", layout="centered")
st.title("📝 Formulário de Avaliação de Viagem")
st.write("Sua avaliação nos ajudará a recomendar suas próximas viagens!")
st.markdown("---")

# --- Configuração do Google Cloud Storage ---
# O Streamlit Community Cloud injeta os "Secrets" como variáveis de ambiente.
try:
    # Tenta carregar as credenciais do JSON armazenado no Streamlit Secrets
    gcp_creds_dict = json.loads(st.secrets["gcp_service_account_json"])
    storage_client = storage.Client.from_service_account_info(gcp_creds_dict)
    BUCKET_NAME = st.secrets["gcs_bucket_name"]
except Exception as e:
    st.error(f"Erro ao configurar o acesso ao Google Cloud Storage. Verifique os 'Secrets' do Streamlit. Erro: {e}")
    storage_client = None
    BUCKET_NAME = None

# --- Formulário de Coleta ---
with st.form("avaliacao_form", clear_on_submit=True):
    st.subheader("Detalhes da Viagem")
    id_cliente = st.text_input("Seu ID de Cliente", help="Insira seu identificador único (ex: cliente123).")
    destino = st.text_input("Destino da Viagem", placeholder="Ex: Salvador, BA")
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data de Início", value=datetime.today(), max_value=datetime.today())
    with col2:
        data_fim = st.date_input("Data de Fim", value=datetime.today(), max_value=datetime.today())

    st.subheader("Sua Avaliação")
    nota_experiencia = st.slider("Nota para a Experiência Geral (0-5)", 0, 5, 3)
    nota_destino = st.slider("Nota para o Destino Visitado (0-5)", 0, 5, 3)

    submitted = st.form_submit_button("✔️ Enviar Avaliação")

# --- Lógica de Processamento ao Enviar ---
if submitted and storage_client:
    if not id_cliente or not destino:
        st.error("Por favor, preencha os campos 'ID do Cliente' e 'Destino'.")
    elif data_fim < data_inicio:
        st.error("A 'Data de Fim' não pode ser anterior à 'Data de Início'.")
    else:
        nova_avaliacao = {
            'id_cliente': [id_cliente],
            'destino': [destino],
            'data_inicio': [data_inicio.strftime('%Y-%m-%d')],
            'data_fim': [data_fim.strftime('%Y-%m-%d')],
            'nota_experiencia': [nota_experiencia],
            'nota_destino': [nota_destino]
        }
        df_nova_avaliacao = pd.DataFrame(nova_avaliacao)

        # Converte o DataFrame para CSV em formato de string
        csv_string = df_nova_avaliacao.to_csv(index=False)

        # Define o nome do arquivo no bucket
        file_name = "novas_avaliacoes.csv"

        try:
            # Faz o upload do arquivo para o GCS
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(file_name)
            blob.upload_from_string(csv_string, 'text/csv')
            st.success(f"✅ Avaliação enviada com sucesso! O pipeline do Airflow irá processá-la em breve.")
        except Exception as e:
            st.error(f"Falha ao enviar avaliação para o servidor. Tente novamente. Erro: {e}")
