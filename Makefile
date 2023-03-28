all: bench readme valid map
	
bench:
	cldfbench makecldf cldfbench_cariban_meta.py 

readme:
	cldf markdown cldf/metadata.json > cldf/README.md

valid:
	cldf validate cldf/metadata.json

map:
	python3 map.py

bib:
	biblatex2bibtex /home/florianm/Dropbox/research/cariban/cariban_references.bib --output etc/sources.bib