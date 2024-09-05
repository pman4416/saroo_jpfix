#!/bin/bash

fontjp=font_shnmk14.bin
ssfirm=ssfirm.bin

if [ ! -f ${ssfirm} ]; then
	echo "Cannot find firmware: ${ssfirm}"
	exit 2
fi

if [ ! -f ${fontjp} ]; then
	echo "Cannot find fontjp data: ${fontjp}"
	exit 2
fi

mv ${ssfirm} ${ssfirm}.org
dd if=${ssfirm}.org of=${ssfirm} count=256
cat ${fontjp} >> ${ssfirm}
