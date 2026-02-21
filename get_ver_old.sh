#!/usr/bin/env bash

OUTPUT="$(git describe --abbrev=0 --tags)"
OUTPUT=${OUTPUT//./_}
CDATE="$(date +%Y_%m_%d)"
echo "${OUTPUT}"_"${CDATE}" > ./version.txt
