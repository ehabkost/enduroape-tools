for d in `seq 0 9`;do echo DIGITO: $d;for n in 2 1;do echo $n...;sleep 1;done;echo gravando:;arecord -D front:CARD=default,DEV=0 -f cd -c 1 sounds/digits/$d.wav;done
