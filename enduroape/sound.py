# -*- coding: utf-8 -*-

import subprocess, sys

import logging

logger = logging.getLogger('enduroape.sound')
dbg = logger.debug
info = logger.info
warn = logger.warn
error = logger.error

# raw sound file specs:
RATE=44100
SOXENC='signed-integer'
BYTES=2
BITS=BYTES*8

SOX_ARGS = ['-t', 'raw', '-r', str(RATE), '-e', SOXENC, '-b', str(BITS)]

MAX_SAMPLES = 1024*1024 # maximum number of samples handled at once, to avoid allocating too much memory

TRECHO_LONGO = 50

class SoundGenerator:
    def silence(self, samples):
        while samples > 0:
            n = min(samples, MAX_SAMPLES)
            self.write('\0'*BYTES*n, n)
            samples -= n

    def sox_cmd(self, args, samples=-1, wait=True):
        dbg('sox command: sox %r', args)
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

    def sine(self, time, freq):
        return self.sox_effect(['synth', '%.5f' % (time), 'sine', str(freq), 'gain', '-3'])
 
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

    def say_time(self, seconds):
        seconds = int(seconds)
        minutes = seconds/60
        seconds = seconds%60

        if minutes > 0:
            self.number(minutes)
            self.word('minutos')
        self.number(seconds)
        self.word('segundos')

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

    def metronome(self, bpm, t):
        beat_length = 60/float(bpm)
        last_beat = t-beat_length

        beat = MemoryTrack()
        beat.wav_file('sounds/click.wav')

        now = self.cur_time()
        while self.cur_time() < last_beat:
            self.mem_tracks(beat)
            now += beat_length
            self.silence_to(now)


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

def generate_soundtrack(opts, items):
    proc = subprocess.Popen(['sox']+SOX_ARGS+['-','-t','wav',opts.soundfile], stdin=subprocess.PIPE)
    f = proc.stdin
    w = SoundWriter(f)

    def silence_to(t):
        if opts.no_silence:
            w.silence(RATE) # silêncio de 1 segundo apenas, para facilitar
            return True

        return w.silence_to(t)

    trecholongo = word_track('trecholongo')
    distnext = word_track('distanciaparaproxima')
    distancia = word_track('distancia')
    metros = word_track('metros')
    passos = word_track('passos')

    worst_late = None
    worst_late_delay = 0

    for state,i in items:
        if i.is_a('Referencia'):
            dbg("abs_time: %r", i.abs_time)
            dbg("we're at: %r", w.cur_time())

            npassos = number_track(int(i.rel_passos))
            nmetros = number_track(i.rel_dist)

            desc = MemoryTrack()
            desc.wav_file('%s/ref%d.wav' % (opts.instructions_dir, i.ref_index))
            before_desc = i.abs_time - desc.seconds

            remaining = w.time_to(before_desc)
            if i.rel_dist == 0:
                pass
            elif i.rel_dist > TRECHO_LONGO:
                w.mem_tracks(trecholongo)
                w.mem_tracks(distancia, npassos, passos)
            elif False: ### remaining > seconds(distnext, npassos, passos, nmetros, metros):
                w.mem_tracks(distnext, npassos, passos, nmetros, metros)
            elif remaining > seconds(distnext, npassos, passos):
                w.mem_tracks(distnext, npassos, passos)
            elif remaining > seconds(distancia, npassos, passos):
                w.mem_tracks(distancia, npassos, passos)
            else:
                info("sem tempo para aviso de passos. ref_id: %r", i.ref_id)

            remaining = w.time_to(before_desc)
            late = (remaining < 0)
            if not late:
                w.metronome(state.cur_trecho.steps_bpm, before_desc)
            else:
                late = True
                delay = w.cur_time()-before_desc
                warn("Pouco tempo para o som. atraso de %.2f segundos Ref: %r. Tempo ref: %.2f. tempo som: %.2f. instruções: %.2f s", delay, i.ref_id, i.abs_time, w.cur_time(), desc.seconds)
                if delay > worst_late_delay:
                    worst_late_delay = delay
                    worst_late = i

            w.mem_tracks(desc)
            if not silence_to(i.abs_time):
                delay = w.cur_time()-i.abs_time
                if not late:
                    # isso não deveria acontecer
                    error(u"Panico: não deu tempo de dizer o número da referência? (%.2f secs)", delay)

            w.word('referencia')
            w.number(i.ref_index)

            dbg("we're now at: %r", w.cur_time())
        elif i.is_a('Neutro'):
            tempo = i.abs_time-state.prev_abs_time

            w.word('neutrode')
            w.say_time(tempo)

            if not silence_to(i.abs_time-10):
                warn("Sem tempo para avisar do fim do neutro! (-10s)")
            w.word('10-segundos-neutro')

            if not silence_to(i.abs_time):
                warn("Sem tempo para avisar do fim do neutro! (final)")
            w.word('neutro-acabou')
        elif i.is_a('NovoTrecho'):
            w.word('novo-trecho')
            #w.number(i.number)
            #w.word('velocidade')
            w.number(i.speed)
            w.word('metros-por-segundo')
        elif i.is_a('NewPage'):
            w.word('nova-pagina')
            w.number(i.number)

    f.close()
    proc.wait()

    if worst_late is not None:
        info("Pior atraso: %.2f segundos (referencia: %r)", worst_late_delay, worst_late.ref_id)
