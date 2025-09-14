import streamlit as st
import pandas as pd
from datetime import datetime
from google.cloud import storage
import json
import os

st.set_page_config(page_title="Coleta de Avaliação", layout="centered")
st.title("📝 Formulário de Avaliação de Viagem")

# Configuração do GCS
try:
    # Para rodar localmente no Docker, as credenciais vêm do arquivo montado
    storage_client = storage.Client.from_service_account_json("gcp-credentials.json")
    with open("gcs_bucket_name.txt", "r") as f:
        BUCKET_NAME = f.read().strip()
except Exception as e:
    st.error(f"Erro ao configurar o GCS: {e}")
    storage_client = None

# ... (resto do formulário igual ao que você já tem) ...
# Lembre-se de adicionar todos os campos do formulário aqui
with st.form("avaliacao_form", clear_on_submit=True):
    id_cliente = st.text_input("Seu ID de Cliente")
    destino = st.text_input("Destino da Viagem")
    data_inicio = st.date_input("Data de Início")
    data_fim = st.date_input("Data de Fim")
    nota_experiencia = st.slider("Nota para a Experiência Geral (0-5)", 0, 5, 3)
    nota_destino = st.slider("Nota para o Destino Visitado (0-5)", 0, 5, 3)
    submitted = st.form_submit_button("✔️ Enviar Avaliação")

if submitted and storage_client:
    # ... (lógica para criar o DataFrame é a mesma) ...
    nova_avaliacao = {'id_cliente': [id_cliente], 'destino': [destino], 'data_inicio': [data_inicio.strftime('%Y-%m-%d')], 'data_fim': [data_fim.strftime('%Y-%m-%d')], 'nota_experiencia': [nota_experiencia], 'nota_destino': [nota_destino]}
    df_nova_avaliacao = pd.DataFrame(nova_avaliacao)
    csv_string = df_nova_avaliacao.to_csv(index=False)

    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob("novas_avaliacoes.csv")
        blob.upload_from_string(csv_string, 'text/csv')
        st.success(f"✅ Avaliação enviada! O pipeline irá processá-la.")
    except Exception as e:
        st.error(f"Falha ao enviar avaliação: {e}")
