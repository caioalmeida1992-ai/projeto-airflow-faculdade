import pandas as pd
from datetime import datetime
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from io import BytesIO # <-- IMPORTANTE ADICIONAR ESTA LINHA

BUCKET_NAME = "bucket-dados-viagens" # Verifique se este é o nome correto do seu bucket
SOURCE_FILE_NAME = "novas_avaliacoes.csv"

def run_etl():
    """Função principal que orquestra a execução do ETL na nuvem."""
    print("--- Iniciando Pipeline de ETL de Viagens na Nuvem ---")
    
    gcs_hook = GCSHook(gcp_conn_id='google_cloud_default')
    
    # 1. Extrair
    if not gcs_hook.exists(bucket_name=BUCKET_NAME, object_name=SOURCE_FILE_NAME):
        print("Nenhum arquivo novo para processar.")
        return

    print(f"Extraindo dados de gs://{BUCKET_NAME}/{SOURCE_FILE_NAME}...")
    # --- BLOCO CORRIGIDO ---
    # Baixa o conteúdo do arquivo em memória (bytes)
    file_bytes = gcs_hook.download(bucket_name=BUCKET_NAME, object_name=SOURCE_FILE_NAME)
    # Usa o pandas para ler os bytes como se fossem um arquivo
    df_raw = pd.read_csv(BytesIO(file_bytes))
    # --- FIM DO BLOCO CORRIGIDO ---

    if df_raw.empty:
        print("Arquivo CSV encontrado, mas está vazio. Arquivando.")
    else:
        # 2. Transformar
        print("Iniciando transformação dos dados...")
        df_raw['data_inicio'] = pd.to_datetime(df_raw['data_inicio'])
        df_raw['data_fim'] = pd.to_datetime(df_raw['data_fim'])
        df_raw['duracao_dias'] = (df_raw['data_fim'] - df_raw['data_inicio']).dt.days
        df_raw['periodo_ferias'] = df_raw['duracao_dias'] > 7
        df_raw['data_processamento'] = datetime.now()
        print("Transformação concluída.")

        # 3. Carregar
        print("Conectando ao MongoDB Atlas...")
        mongo_hook = MongoHook(mongo_conn_id='mongo_atlas')
        client = mongo_hook.get_conn()
        db = client.get_database("empresa_onibus")
        collection = db.get_collection("viagens")
        
        data_dict = df_raw.to_dict("records")
        print(f"Inserindo {len(data_dict)} registros na coleção 'viagens'...")
        collection.insert_many(data_dict)
        client.close()
        print("Dados carregados com sucesso no MongoDB.")

    # 4. Arquivar (roda mesmo se o arquivo estiver vazio, para limpar a fila)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_file_name = f"arquivados/{timestamp}_{SOURCE_FILE_NAME}"
    print(f"Arquivando arquivo para gs://{BUCKET_NAME}/{archive_file_name}...")
    gcs_hook.copy(source_bucket=BUCKET_NAME, source_object=SOURCE_FILE_NAME,
                  dest_bucket=BUCKET_NAME, dest_object=archive_file_name)
    gcs_hook.delete(bucket_name=BUCKET_NAME, object_name=SOURCE_FILE_NAME)
    print("Arquivo arquivado com sucesso.")
    
    print("--- Pipeline de ETL de Viagens Concluído ---")
