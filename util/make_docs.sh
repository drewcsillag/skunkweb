#! /bin/bash

DOCSDIR=$(dirname $PWD)/docs
echo $DOCSDIR

cwd=`pwd`
for i in stmlrefer PyDO devel opman 
do
  cd ${DOCSDIR}/html
  make ${i}/${i}.html && rm *.{dat,ind,pl} ${i}.* ${i}/WARNINGS ${i}/*.{how,aux,idx,log,pl,tex}
  cd ${DOCSDIR}/paper-letter
  make ${i}.pdf &&  rm *.{log,l2h,idx,ind,aux,how,ilg,toc}
done
cd $cwd
