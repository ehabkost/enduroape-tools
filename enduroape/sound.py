
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
            self.gen('\0'*BYTES*n, n)
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

            self.gen(data, n)
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


class SoundWriter(SoundGenerator):
    def __init__(self, raw_out):
        self.raw_out = raw_out
        self.samples = 0

    def gen(self, b, samples):
        """Write raw samples

        The 'samples' parameter is just a sanity check to make sure
        the data is correct
        """
        assert type(b) == str and len(b) == BYTES*samples
        self.raw_out.write(b)
        self.samples += samples

    def cur_time(self):
        return self.samples/float(RATE)

    def samples_to(self, t):
        """Number of samples needed to go to time 't'"""
        cur = self.cur_time()
        if cur > t:
            raise Exception("too late. we are already past %r (we're at %r)" % (t, cur))
        return int((t-cur)*RATE)


def generate_soundtrack(filename, items):
    proc = subprocess.Popen(['sox']+SOX_ARGS+['-','-t','wav',filename], stdin=subprocess.PIPE)
    f = proc.stdin
    w = SoundWriter(f)
    for state,i in items:
        if i.is_a('Referencia') or i.is_a('Neutro'):
            dbg("abs_time: %r", i.abs_time)
            dbg("we're at: %r", w.cur_time())
            if i.abs_time > w.cur_time():
                w.silence(w.samples_to(i.abs_time))
            else:
                info("Pouco tempo para o som. Ref: %r. Tempo ref: %r. Trmepo som: %r", i.ref_id, i.abs_time, w.cur_time())
            dbg("we're now at: %r", w.cur_time())
            w.word('referencia')
            w.number(int(i.ref_id))
            w.wav_file('sounds/instrucoes/2010-11/ref%s.wav' % (i.ref_id))

    f.close()
    proc.wait()
