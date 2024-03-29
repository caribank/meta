.PHONY: cldf

cldf: bench readme valid
	
all: bib bench readme valid map
	
bench:
	cldfbench makecldf cldfbench_cariban_meta.py 

readme:
	cldf markdown cldf/metadata.json > cldf/README.md

valid:
	cldf validate cldf/metadata.json

map:
	python3 map.py

bib: bibload bibpdf bibrun

bibpdf:
	python etc/bib_pdf.py

bibload:
	biblatex2bibtex /home/florianm/Dropbox/research/cariban/cariban_references.bib --output bib/sources.bib

bibrun:
	pandoc --pdf-engine=xelatex -o bib/bibliography.pdf bib/bibliography.md --bibliography bib/sources.bib --citeproc
	pandoc -o bib/README.md bib/bibliography.md --bibliography bib/sources_web.bib --citeproc -t markdown-citations --csl etc/chicago-author-date-mod.csl
	perl -pi -e 's/::: {.*? .csl-entry}//g' bib/README.md
	perl -pi -e 's/::://g' bib/README.md
	perl -pi -e 's/{#refs .references .csl-bib-body .hanging-indent}//g' bib/README.md
	perl -pi -e 's/{#sources .unnumbered}//g' bib/README.md
	perl -pi -e 's/PDFLINK/[Request PDF]/g' bib/README.md