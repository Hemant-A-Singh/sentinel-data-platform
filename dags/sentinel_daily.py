from datetime import datetime

from airflow.sdk import dag, DAG, task
from airflow.providers.standard.operators.python import PythonOperator

from sentinel.extract.raw_orders import main as load_raw_orders

# with DAG(
#     dag_id="sentinel_daily",
#     start_date=datetime(2026, 10, 1),
#     schedule="@daily",
#     catchup=False,
#     tags=["sentinel"],
# ) as dag:
#     extract = PythonOperator(
#         task_id="extract_orders",
#         python_callable=load_raw_orders,
#         op_kwargs={"run_date": "{{ ds }}"},
#     )

@dag
def sentinel_daily_task_method():

    @task.python
    def print_task():
        print("Dag started running")

    @task.python
    def extract_orders():
        load_raw_orders()

    first = print_task()
    second = extract_orders()

    first >> second

sentinel_daily_task_method()


