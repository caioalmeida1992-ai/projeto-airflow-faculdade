from __future__ import annotations
import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator

# Importa a função principal do nosso script de ETL
from etl_script import run_etl

# Definição da DAG
with DAG(
        dag_id="pipeline_processamento_viagens",
        start_date=pendulum.datetime(2025, 8, 23, tz="America/Sao_Paulo"),
        schedule_interval="*/10 * * * *",  # Executa a cada 10 minutos
        catchup=False,
        tags=["projeto_faculdade", "etl"],
        doc_md="""
    DAG para processar avaliações de viagens enviadas pelos clientes (Versão WSL).
    - Extrai dados de um arquivo CSV.
    - Transforma e enriquece os dados.
    - Carrega os dados no MongoDB.
    - Arquiva o CSV processado.
    """
) as dag:
    processar_avaliacoes_task = PythonOperator(
        task_id="executar_etl_de_viagens",
        python_callable=run_etl
    )