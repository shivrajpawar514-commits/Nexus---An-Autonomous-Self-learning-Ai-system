.PHONY: install test eval run learn clean dashboard

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

eval:
	python -m eval.run --split test

learn:
	python main.py learn --cycles 3

stats:
	python main.py stats

dashboard:
	python main.py dashboard --port 8080

clean:
	rm -rf __pycache__ .pytest_cache *.db sandbox_workspace/*.py

