
import subprocess, sys

import logging

logger = logging.getLogger('enduroape.sound')
info = logger.info
dbg = logger.debug

# raw sound file specs:
RATE=44100
SOXENC='signed-integer'
BYTES=2
BITS=BYTES*8

SOX_ARGS = ['-t', 'raw', '-r', str(RATE), '-e', SOXENC, '-b', str(BITS)]

MAX_SAMPLES = 65536 # maximum number of samples handled at once, to avoid allocating too much memory

class SoundGenerator:
    def silence(self, samples):
        while samples > 0:
            n = min(samples, MAX_SAMPLES)
            self.write('\0'*BYTES*n, n)
            samples -= n

    def sox_cmd(self, args, samples=-1, wait=True):
        proc = subprocess.Popen(['sox']+args, stdout=subprocess.PIPE)
        s = samples
        while (samples < 0) or (s > 0):
            n = min(samples, MAX_SAMPLES)
            data = proc.stdout.read(n*BYTES)
            if data == '':
                break

            bytes = len(data)
            assert (bytes % BYTES) == 0 # whole number of samples
            n = bytes/BYTES

            self.write(data, n)
            s -= n
        if wait:
            proc.wait()
            if proc.returncode <> 0:
                raise Exception('sox error')

    def sox_effect(self, args):
        return self.sox_cmd(['-n']+SOX_ARGS+['-']+args)
 
    def wav_file(self, file):
        return self.sox_cmd(['-t','wav',file]+SOX_ARGS+['-'])

    def word(self, word):
        return self.wav_file('sounds/words/%s.wav' % (word))

    def digit(self, d):
        return self.wav_file('sounds/digits/%s.wav' % (d))

    def number(self, n):
        s = str(n)
        for digit in s:
            self.digit(digit)


class MemoryTrack(SoundGenerator):
    def __init__(self):
        self.data = []
        self.samples = 0

    @property
    def seconds(self):
        return self.samples/float(RATE)

    def write(self, b, samples):
        self.data.append( (b, samples) )
        self.samples += samples

    def write_to(self, other):
        for b, samples in self.data:
            other.write(b, samples)

class SoundWriter(SoundGenerator):
    def __init__(self, raw_out):
        self.raw_out = raw_out
        self.samples = 0

    def write(self, b, samples):
        """Write raw samples

        The 'samples' parameter is just a sanity check to make sure
        the data is correct
        """
        assert type(b) == str and len(b) == BYTES*samples
        self.raw_out.write(b)
        self.samples += samples

    def cur_time(self):
        return self.samples/float(RATE)

    def time_to(self, t):
        return t-self.cur_time()

    def samples_to(self, t):
        """Number of samples needed to go to time 't'"""
        return int(self.time_to(t)*RATE)

    def silence_to(self, t):
        samples = self.samples_to(t)
        if samples < 0:
            return False
        self.silence(samples)
        return True

    def mem_tracks(self, *tracks):
        for t in tracks:
            t.write_to(self)

def word_track(word):
    t = MemoryTrack()
    t.word(word)
    return t

def number_track(n):
    t = MemoryTrack()
    t.number(n)
    return t

def seconds(*tracks):
    return sum(t.seconds for t in tracks)

def generate_soundtrack(filename, items):
    proc = subprocess.Popen(['sox']+SOX_ARGS+['-','-t','wav',filename], stdin=subprocess.PIPE)
    f = proc.stdin
    w = SoundWriter(f)

    distnext = word_track('distanciaparaproxima')
    distancia = word_track('distancia')
    metros = word_track('metros')
    passos = word_track('passos')

    for state,i in items:
        if i.is_a('Referencia'):
            dbg("abs_time: %r", i.abs_time)
            dbg("we're at: %r", w.cur_time())

            npassos = number_track(int(i.rel_passos))
            nmetros = number_track(i.rel_dist)

            remaining = w.time_to(i.abs_time)
            if False: ### remaining > seconds(distnext, npassos, passos, nmetros, metros):
                w.mem_tracks(distnext, npassos, passos, nmetros, metros)
            elif remaining > seconds(distnext, npassos, passos):
                w.mem_tracks(distnext, npassos, passos)
            elif remaining > seconds(distancia, npassos, passos):
                w.mem_tracks(distancia, npassos, passos)
            else:
                info("sem tempo para aviso de passos. ref_id: %r", i.ref_id)

            desc = MemoryTrack()
            desc.wav_file('sounds/instrucoes/2010-11/ref%d.wav' % (i.ref_index))
            desc.word('referencia')
            desc.number(i.ref_index)

            before_desc = i.abs_time - desc.seconds
            if not w.silence_to(before_desc):
                info("Pouco tempo para o som. atraso de %r segundos Ref: %r. Tempo ref: %r. tempo som: %r", w.cur_time()-before_desc, i.ref_id, i.abs_time, w.cur_time())

            w.mem_tracks(desc)
            dbg("we're now at: %r", w.cur_time())
        elif i.is_a('Neutro'):
            tempo = i.abs_time-state.prev_abs_time

            w.word('neutrode')
            w.number(tempo)
            w.word('segundos')

            w.silence_to(i.abs_time-10)
            w.word('10-segundos-neutro')
            w.silence_to(i.abs_time)
            w.word('neutro-acabou')

    f.close()
    proc.wait()
