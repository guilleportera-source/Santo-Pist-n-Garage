#!/bin/bash
# Acabado tipo iPhone: estabilización suave, limpieza temporal, color natural y audio limpio a −14 LUFS.
# Uso: finish.sh <carpeta_fotogramas_sr> <video_original> <salida.mp4>
set -e
SR=$1; V=$2; OUT=$3; T=$(dirname $OUT)/_tmp_$$
mkdir -p $T
# 1) secuencia SR -> intermedio sin pérdidas visibles
ffmpeg -v error -y -framerate 30 -i $SR/%05d.jpg -c:v libx264 -crf 10 -preset veryfast -pix_fmt yuv420p $T/sr.mp4
# 2) estabilización (dos pasadas), suave para mantener la sensación de mano
ffmpeg -v error -y -i $T/sr.mp4 -vf vidstabdetect=shakiness=6:accuracy=12:result=$T/t.trf -f null -
# 3) cadena final de vídeo + audio
VF="vidstabtransform=input=$T/t.trf:smoothing=12:optzoom=2:zoomspeed=0.1:interpol=bicubic,\
hqdn3d=1.0:1.0:1.5:1.5,\
eq=contrast=1.06:brightness=0.005:saturation=1.10:gamma=1.02,\
colorbalance=rs=-0.01:bs=0.015:rh=0.02:bh=-0.02,\
cas=0.25,\
scale=1080:1920:flags=lanczos,format=yuv420p"
AF="highpass=f=70,afftdn=nf=-28:tn=1,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,loudnorm=I=-14:TP=-1.5:LRA=9"
ffmpeg -v error -y -i $T/sr.mp4 -i $V -map 0:v -map 1:a -vf "$VF" -af "$AF" \
  -c:v libx264 -profile:v high -preset slow -crf 18 -maxrate 11M -bufsize 22M -r 30 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart $OUT
rm -rf $T
echo ok
