#!/bin/bash
set -e

#THIS SCRIPT MOVES THE FILES FROM BLANK INTO THE PRIVATE REPO

# Directory of current file
bindir=`dirname $0`
bindir=`cd $bindir; pwd`
echo $bindir


LISTFILE="./paths.txt"
while read FILE; do
	echo $FILE
	# Get filename
	FILENAME="${FILE##*/}"
	# Get directory of file that was just moved
	DIRNAME=$(dirname $FILE)
	cp $bindir/blanks/$FILE $bindir/../$DIRNAME
done < $LISTFILE
echo "Done!"

