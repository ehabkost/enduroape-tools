
RATE=44100
ENC='signed-integer'
BITS=16
BYTES=2

SOXRAW="-t raw -r $RATE $ENC -b $BITS"

AREC="arecord -D front:CARD=default,DEV=0 -f cd -c 1"

_wav2raw()
{
	local f="$1"
	local o="${f/.wav/.raw}"
	sox -t wav "$f" $SOXRAW "$o"
}

wav2raw()
{
	local f
	for f;do
		_wav2raw "$f"
	done
}

rplay()
{
	sox $SOXRAW "$1" -t alsa
}

makesilence()
{
	local samples="$1"
	dd if=/dev/zero bs="$BYTES" count="$samples" status=noxfer 2>/dev/null
}

recrefs()
{
	local ref
	for ref;do
		saynumber "$ref" &
		echo REFERENCIA: $ref
		read -p "press enter"
		for n in 2 1;do
			echo $n...
			sleep 1;
		done
		echo 'ACTION!'
		$AREC sounds/instrucoes/2010-11/ref$ref.wav
	done
}

_saynumber()
{
	local d
	local n="$1"
	(
	for d in $(echo "$n" | sed -e 's/./& /g');do
		cat sounds/digits/$d.raw
	done
	)
}
