.PHONY: verify
verify:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
	PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_release.py
	find scripts benchmarks/tools -type f -name '*.sh' -exec bash -n {} +
	python3 -c "import ast,pathlib; [ast.parse(p.read_text()) for root in ('scripts','benchmarks/tools','tests') for p in pathlib.Path(root).glob('*.py')]"
