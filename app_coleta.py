import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Avaliação de Viagem - Clickbus", layout="centered")

st.title("📝 Formulário de Avaliação de Viagem")
st.write(
    "Olá! Por favor, preencha os campos abaixo para registrar a sua experiência com a Clickbus. "
    "Sua avaliação nos ajudará a recomendar suas próximas viagens!"
)
st.markdown("---")

CSV_FILE = 'data/novas_avaliacoes.csv'

# --- Formulário de Coleta ---
# Usar st.form garante que a página não recarregue a cada interação do usuário,
# apenas quando o botão de envio dentro do formulário for clicado.
with st.form("avaliacao_form", clear_on_submit=True):
    st.subheader("Detalhes da Viagem")

    # Campos do formulário
    id_cliente = st.text_input(
        "Seu ID de Cliente",
        help="Insira seu identificador único de cliente (ex: cliente123)."
    )
    destino = st.text_input(
        "Destino da Viagem",
        placeholder="Ex: Salvador, BA"
    )

    # Organiza as datas
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input(
            "Data de Início",
            value=datetime.today(),
            max_value=datetime.today()
        )
    with col2:
        data_fim = st.date_input(
            "Data de Fim",
            value=datetime.today(),
            max_value=datetime.today()
        )

    st.subheader("Sua Avaliação")
    nota_experiencia = st.slider(
        "Nota para a Experiência Geral da Viagem (de 0 a 5)",
        min_value=0,
        max_value=5,
        value=3  # Valor padrão
    )
    nota_destino = st.slider(
        "Nota para o Destino Visitado (de 0 a 5)",
        min_value=0,
        max_value=5,
        value=3  # Valor padrão
    )

    # Botão de envio do formulário
    submitted = st.form_submit_button("✔️ Enviar Avaliação")

# --- Lógica de Processamento ao Enviar ---
if submitted:
    # Validação simples dos campos
    if not id_cliente or not destino:
        st.error("Por favor, preencha os campos 'ID do Cliente' e 'Destino'.")
    elif data_fim < data_inicio:
        st.error("A 'Data de Fim' não pode ser anterior à 'Data de Início'.")
    else:
        # Salva tudo num dicionário que será convertido depois
        nova_avaliacao = {
            'id_cliente': [id_cliente],
            'destino': [destino],
            'data_inicio': [data_inicio.strftime('%Y-%m-%d')],
            'data_fim': [data_fim.strftime('%Y-%m-%d')],
            'nota_experiencia': [nota_experiencia],
            'nota_destino': [nota_destino]
        }

        # Converte o dic para um DataFrame
        df_nova_avaliacao = pd.DataFrame(nova_avaliacao)

        # Lógica para salvar no arquivo CSV
        # Verifica se o arquivo já existe para decidir se escreve o cabeçalho
        header = not os.path.exists(CSV_FILE)

        df_nova_avaliacao.to_csv(
            CSV_FILE,  # Nome do arquivo
            mode='a',  # 'a' para 'append' (adicionar ao final do arquivo)
            header=header,  # Escreve o cabeçalho apenas se o arquivo não existir
            index=False  # Não salva o índice do DataFrame no arquivo
        )

        st.success("✅ Avaliação enviada com sucesso! Obrigado por contribuir.")

# --- Trecho opcional para visualização dos dados brutos na própria página após serem inseridos---
# --- Serve também como uma reafirmação de que o cadastro foi realizado, além da mensagem de sucesso
st.markdown("---")
st.header("Dados Brutos Aguardando Processamento")

if os.path.exists(CSV_FILE):
    df_raw = pd.read_csv(CSV_FILE)
    st.dataframe(df_raw)
else:
    st.info("Ainda não há avaliações para serem processadas. Envie a primeira!")