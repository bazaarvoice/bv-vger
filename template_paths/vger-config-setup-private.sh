#!/bin/bash
set -e

#THIS SCRIPT MOVES THE FILES FROM PRIVATE INTO THE PUBLIC REPO

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
	cp $bindir/private/$FILE $bindir/../$DIRNAME
done < $LISTFILE
echo "Done!"

