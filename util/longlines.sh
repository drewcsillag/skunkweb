#! /bin/bash

########################################################################
# script that finds long lines in source code files and prints the offending
# lines to stdout.  Defaults to searching for python files.
# $Id: longlines.sh 1722 2006-03-11 20:55:32Z smulloni $
# Time-stamp: <01/04/24 13:08:24 smulloni>
########################################################################

function help() {
    printf "$0 [options]  where options are:\n"
    printf "\n"
    printf %b "-h:        print this message and exit\n"
    printf %b "-l [num]:  minimum line length detected. default: 80\n"
    printf %b "-g [glob]: glob used to find files. default: *.py\n"
    printf %b "-r:        search recursively\n"
    printf %b "-d:        directory to search. default: current directory\n"
    printf %b "\n"
    exit 0
}

myGlob="*.py"
len=80
myDir="."
depthArg="-maxdepth 0"
while getopts "hrg:l:d:" opts
do
    case "$opts" in
    g) myGlob=$OPTARG;;
    l) len=$OPTARG;;
    h) help;;
    r) depthArg="";;
    d) myDir=$OPTARG;;
    ?) exit 1;;
    esac
done

find "$myDir" $depthArg -name "$myGlob" -print | xargs grep -n ".\{$len,\}" 
exit 0

########################################################################
# $Log: longlines.sh,v $
# Revision 1.1  2001/08/05 14:59:20  drew_csillag
# Initial revision
#
# Revision 1.2  2001/04/24 21:43:02  smullyan
# fixed bug in httpd.protocol (was accidentally removing line return after
# HTTP response line, producing weirdness).  Removed call of deprecated
# method of config object in remote.__init__.py; added list of configuration
# variables that need to be documented to sw.conf.in.
#
# Revision 1.1  2001/04/23 04:55:49  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
########################################################################