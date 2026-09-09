.PHONY: install test validate evaluate evaluate-factors

install:
	python -m pip install -e .

test:
	python -m unittest discover -s tests -v

validate:
	sourceaware validate examples/manifest.synthetic.jsonl

evaluate:
	sourceaware evaluate examples/predictions.synthetic.jsonl

evaluate-factors:
	sourceaware evaluate-factors examples/factor_predictions.synthetic.jsonl
