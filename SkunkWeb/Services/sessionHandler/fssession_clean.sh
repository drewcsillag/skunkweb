#! /bin/sh

function usage 
{
    echo
    echo "usage: `basename $0` [-t expiration] <session_directory>"
    echo
    echo "   a script that purges expired session files from a"
    echo "   SkunkWeb session directory.  The expiration parameter"
    echo "   is measured in minutes, and defaults to thirty."
    exit 1
}

EXPIRATION=30
while getopts "ht:" ARG
do
    case ${ARG} in
    t)
        EXPIRATION=${OPTARG}
        ;;
    *)
        usage
	;;
    esac
done

shift $(($OPTIND - 1))

SESSIONDIR=$1
if [ -z $SESSIONDIR ]
then
   usage

find $SESSIONDIR -type f -amin +$EXPIRATION -a -exec rm {} \;

