# Convenience Makefile for building HTML documentation.  You probably
# need to set TEXINPUTS from the command line for this to be useful,
# unless you actually build the .dvi files in the top level directory.

PAPER=letter
TOPDIR=..
TOOLSDIR=..
PAPERDIR=$(TOPDIR)/paper-$(PAPER)

TEXINPUTS=$(TOPDIR)/paper-$(PAPER):$(TOPDIR)/texinputs:

# Where are the various programs?
PYTHON=	   python
#WEBCHECKER=$(PYTHON) $(TOPDIR)/../Tools/webchecker/webchecker.py
MKHOWTO=   $(TOOLSDIR)/mkhowto --about $(TOPDIR)/html/stdabout.dat \
	        --up-link ../index.html \
		--style style.css
#		--address $(PYTHONDOCS) 
MKHTML=	   $(MKHOWTO) --html -i .

#BUILDINDEX=$(TOOLSDIR)/buildindex.py

PYTHONDOCS='See <i><a href="about.html">About this document...</a></i> for information on suggesting changes.'
HTMLBASE=  file:`pwd`


DOCS = devel opman stmlrefer PyDO
INDEXFILES=devel/devel.html

COMMONPERL= $(TOPDIR)/l2hinit.perl

#$(TOPDIR)/manual.perl \
#	$(TOPDIR)/python.perl \


all:	$(INDEXFILES) 
#index.html modindex.html acks.html

.PHONY: devel

devel: devel/devel.html

# The index.html target is at the end since it screws up font-lock.

devel/devel.html:  ../devel/devel.tex ../devel/ae.tex
	$(MKHTML) $(TOPDIR)/devel/devel.tex

stmlrefer/stmlrefer.html: ../stmlrefer/stmlrefer.tex
	$(MKHTML) $(TOPDIR)/stmlrefer/stmlrefer.tex

opman/opman.html: ../opman/opman.tex
	$(MKHTML) $(TOPDIR)/opman/opman.tex

PyDO/PyDO.html: ../PyDO/PyDO.tex
	$(MKHTML) $(TOPDIR)/PyDO/PyDO.tex

tutorial/tutorial.html: ../tutorial/tutorial.tex
	$(MKHTML) $(TOPDIR)/tutorial/tutorial.tex
clean:
	-rm -rf PyDO opman devel stmlrefer
	-for i in aux dvi how idx ilg ind l2h log tar.gz toc;\
	do \
		for j in $(DOCS);\
		do \
			rm -f $$j.$$i;\
		done;\
	done

	-for i in $(DOCS);\
	do\
		rm mod$$i.ind;\
	done
	-rm intlabels.pl index.dat

distclean realclean clobber: clean
	rm -rf index.html modindex.html acks.html
	rm -rf devel/  devel* moddevel.ind


# This is really ugly, but we're not dependent on $(RELEASE), which isn't
# defined here.  It also maintains the proper dependency on boilerplate.tex.

# It's at the end of the file since it wedges font-lock in XEmacs.

#BOILERPLATE=$(TOPDIR)/texinputs/boilerplate.tex
#index.html: $(TOPDIR)/html/index.html.in $(BOILERPLATE)
#	 REL=`grep '\\release{' $(BOILERPLATE) | sed 's/.*\\release{\(.*\)}.*$$/\1/'`; \
#		 REL=`echo "$$REL" | sed 's/[$$]//g'`; \
#		 sed "s/@RELEASE@/$$REL/g" $< >TEMP
#	 DATE=`grep '\\date{' $(BOILERPLATE) | sed 's/.*\\date{\(.*\)}.*$$/\1/'` ; \
#		 if [ "$$DATE" = '\today' ] ; then DATE=`date '+%B %e, %Y'`;fi;\
#		 sed "s/@DATE@/$$DATE/g" TEMP >$@
#	 rm -f TEMP
