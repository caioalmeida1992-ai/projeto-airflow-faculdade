import pandas as pd
from datetime import datetime
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.providers.google.cloud.hooks.gcs import GCSHook

BUCKET_NAME = "bucket-dados-viagens" # <-- VERIFIQUE SE ESTE É O NOME CORRETO
SOURCE_FILE_NAME = "novas_avaliacoes.csv"

def run_etl():
    gcs_hook = GCSHook(gcp_conn_id='google_cloud_default')

    if not gcs_hook.exists(bucket_name=BUCKET_NAME, object_name=SOURCE_FILE_NAME):
        print("Nenhum arquivo novo para processar.")
        return

    print(f"Extraindo dados de gs://{BUCKET_NAME}/{SOURCE_FILE_NAME}...")
    with gcs_hook.download(bucket_name=BUCKET_NAME, object_name=SOURCE_FILE_NAME) as tmp_file:
        df_raw = pd.read_csv(tmp_file.name)

    # ... (resto da lógica de transformar e carregar no MongoDB é a mesma) ...
    df_raw['data_inicio'] = pd.to_datetime(df_raw['data_inicio'])
    df_raw['data_fim'] = pd.to_datetime(df_raw['data_fim'])
    df_raw['duracao_dias'] = (df_raw['data_fim'] - df_raw['data_inicio']).dt.days
    df_raw['periodo_ferias'] = df_raw['duracao_dias'] > 7
    df_raw['data_processamento'] = datetime.now()

    mongo_hook = MongoHook(mongo_conn_id='mongo_atlas')
    client = mongo_hook.get_conn()
    db = client.get_database("empresa_onibus")
    collection = db.get_collection("viagens")
    data_dict = df_raw.to_dict("records")
    collection.insert_many(data_dict)
    client.close()
    print("Dados carregados com sucesso no MongoDB.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_file_name = f"arquivados/{timestamp}_{SOURCE_FILE_NAME}"
    gcs_hook.copy(source_bucket=BUCKET_NAME, source_object=SOURCE_FILE_NAME,
                  dest_bucket=BUCKET_NAME, dest_object=archive_file_name)
    gcs_hook.delete(bucket_name=BUCKET_NAME, object_name=SOURCE_FILE_NAME)
    print("Arquivo arquivado com sucesso.")
