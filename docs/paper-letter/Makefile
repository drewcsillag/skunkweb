# you could set this to a4
PAPER=letter

# Where are the various programs?
DVIPS=		dvips -N0 -t $(PAPER)
PYTHON=		python

TOOLSDIR=	..

MKHOWTO=	$(TOOLSDIR)/mkhowto
MKDVI=		$(MKHOWTO) --dvi
MKPDF=		$(MKHOWTO) --pdf


# what's what
MANDVIFILES=	stmlrefer.dvi opman.dvi PyDO.dvi devel.dvi
HOWTODVIFILES=	

MANPDFFILES=	stmlrefer.pdf opman.pdf PyDO.pdf devel.pdf
HOWTOPDFFILES=	

MANPSFILES=	stmlrefer.ps opman.ps PyDO.ps devel.ps
HOWTOPSFILES=	

DVIFILES=	$(MANDVIFILES) $(HOWTODVIFILES)
PDFFILES=	$(MANPDFFILES) $(HOWTOPDFFILES)
PSFILES=	$(MANPSFILES) $(HOWTOPSFILES)


#include ../Makefile.deps


SCRIPTS:	  ../indfix.py

$(DVIFILES):	  $(SCRIPTS) $(MKHOWTO)
$(PDFFILES):	  $(SCRIPTS) $(MKHOWTO)


# Rules to build PostScript and PDF formats
.SUFFIXES: .dvi .ps

.dvi.ps:
	$(DVIPS) -o $@ $<


all:	ps
dvi:	$(DVIFILES)
pdf:	$(PDFFILES)
ps:	$(PSFILES)


opman.dvi: ../opman/opman.tex
	$(MKDVI) ../opman/opman.tex

opman.pdf: ../opman/opman.tex
	$(MKPDF) ../opman/opman.tex

devel.dvi: ../devel/devel.tex
	$(MKDVI) ../devel/devel.tex

devel.pdf: ../devel/devel.tex
	$(MKPDF) ../devel/devel.tex

stmlrefer.dvi: ../stmlrefer/stmlrefer.tex
	$(MKDVI) ../stmlrefer/stmlrefer.tex

stmlrefer.pdf: ../stmlrefer/stmlrefer.tex
	$(MKPDF) ../stmlrefer/stmlrefer.tex

PyDO.dvi: ../PyDO/PyDO.tex
	$(MKDVI) ../PyDO/PyDO.tex

PyDO.pdf: ../PyDO/PyDO.tex
	$(MKPDF) ../PyDO/PyDO.tex



clean:
	rm -f *~ *.aux *.idx *.ilg *.ind *.log *.toc *.bkm *.syn *.pla api.tex

clobber: clean
	rm -f $(DVIFILES) $(PSFILES) $(PDFFILES) devel.bib

realclean: clobber
distclean: clobber
