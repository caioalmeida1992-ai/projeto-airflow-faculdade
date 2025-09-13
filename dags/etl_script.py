import pandas as pd
import os
from pymongo import MongoClient
from datetime import datetime

# Constates usadas no script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_FILE_PATH = os.path.join(BASE_DIR, 'data', 'novas_avaliacoes.csv')
ARCHIVE_FOLDER_PATH = os.path.join(BASE_DIR, 'data', 'arquivados')

# tive que alterar a uri padrão da config do mongo porque está dando erro com wsl, tive que especifica o ip
MONGO_URI = "mongodb://172.23.0.1:27017/"
MONGO_DB = "empresa_onibus"
MONGO_COLLECTION = "viagens"


def extract_data(file_path):
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        print(f"Arquivo de origem não encontrado ou vazio: {file_path}")
        return None

    print(f"Extraindo dados de {file_path}...")
    return pd.read_csv(file_path)

# Faz a transformação para os dados do datafreame
def transform_data(df):
    if df is None:
        return None

    print("Iniciando transformação dos dados...")
    df['data_inicio'] = pd.to_datetime(df['data_inicio'])
    df['data_fim'] = pd.to_datetime(df['data_fim'])
    df['duracao_dias'] = (df['data_fim'] - df['data_inicio']).dt.days
    df['periodo_ferias'] = df['duracao_dias'] > 7
    df['data_processamento'] = datetime.now()

    print("Transformação concluída.")
    return df


# Conexão com o mongo e gera alguns logs que eu posso analisar pelo log do airflow, auxilia no troubleshooting tbm
def load_data(df):
    if df is None:
        return

    print(f"Conectando ao MongoDB em {MONGO_URI}...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # O comando abaixo força a conexão e falhará se o servidor não estiver acessível
        client.server_info()
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]

        data_dict = df.to_dict("records")

        print(f"Inserindo {len(data_dict)} registros na coleção '{MONGO_COLLECTION}'...")
        collection.insert_many(data_dict)

        client.close()
        print("Dados carregados com sucesso no MongoDB.")
    except Exception as e:
        print(
            f"ERRO: Não foi possível conectar ou inserir dados no MongoDB. Verifique se ele está rodando no Windows. Erro: {e}")


def archive_file(file_path):
    """Move o arquivo processado para a pasta de arquivados."""
    if not os.path.exists(file_path):
        return

    if not os.path.exists(ARCHIVE_FOLDER_PATH):
        os.makedirs(ARCHIVE_FOLDER_PATH)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = os.path.basename(file_path)
    archive_path = os.path.join(ARCHIVE_FOLDER_PATH, f"{timestamp}_{file_name}")

    os.rename(file_path, archive_path)
    print(f"Arquivo movido para {archive_path}")


def run_etl():
    """Função principal que orquestra a execução do ETL."""
    print("--- Iniciando Pipeline de ETL de Viagens ---")
    df_raw = extract_data(SOURCE_FILE_PATH)

    if df_raw is not None:
        df_transformed = transform_data(df_raw)
        load_data(df_transformed)
        archive_file(SOURCE_FILE_PATH)
    else:
        print("Nenhum dado novo para processar.")

    print("--- Pipeline de ETL de Viagens Concluído ---")