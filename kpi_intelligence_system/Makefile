.PHONY: install data etl kpi dashboard api scheduler test clean

install:
	pip install -r requirements.txt

data:
	python -m kpi_system.etl.generate_sample_data

etl:
	python scripts/run_etl.py

kpi:
	python scripts/run_kpi.py

dashboard:
	streamlit run src/kpi_system/dashboard/app.py

api:
	uvicorn kpi_system.api.main:app --reload --port 8000

scheduler:
	python scripts/run_scheduler.py

test:
	PYTHONPATH=src pytest -q

clean:
	rm -rf data/raw/*.csv data/processed/*.csv data/warehouse/*.db
