RST2HTML=/usr/bin/docutils-html.py
RST2LATEX=/usr/bin/docutils-rst2latex.py
PDFLATEX=/usr/bin/pdflatex

FILES=ae_tut.txt config.txt extending.txt index.txt installation.txt preface.txt services.txt stmlref.txt

manual.html: ${FILES}
	${RST2HTML} index.txt manual.html

manual.tex: ${FILES}
	${RST2LATEX} index.txt manual.tex

manual.pdf: manual.tex
	${PDFLATEX} manual.tex

clean:
	-rm *.html *.tex *.out *.log *.aux *.pdf
