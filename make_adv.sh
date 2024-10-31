#!/usr/bin/env bash

# ---- Configuration variables ----------
# Name of the game
GAME="test"
# This name will be used as:
#   - The file to compile will be test.cyd with this example
#   - The name of the TAP file or +3 disk image
#
# Target for the compiler (48k, 128k for TAP, plus3 for DSK)
TARGET="48k"
#
# Number of lines used on SCR files at compressing
IMGLINES="192"
#
# Loading screen
LOAD_SCR="./LOAD.scr"
#
# Parameters for compiler
CYDC_EXTRA_PARAMS=
# --------------------------------------

#Check if python is installed
command -v python >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "---------------------"
    echo "Python not installed!"
    exit 1
fi

# To resolve current dir of the script on the DIR variable
SOURCE=${BASH_SOURCE[0]}
while [ -L "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
  SOURCE=$(readlink "$SOURCE")
  [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )

python $DIR/make_adventure.py -n $GAME $CYDC_EXTRA_PARAMS -il $IMGLINES -scr $LOAD_SCR $TARGET
RETVAL=$?
if [ $RETVAL -ne 0 ]; then
    echo "---------------------"
    echo "Compile error, please check"
    read -rsp $'Press enter to continue...\n'
else
    echo "---------------------"
    echo "Success!"
fi
exit $RETVAL
