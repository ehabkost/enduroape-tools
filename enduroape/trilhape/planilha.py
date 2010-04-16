#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Parsing de planilhas do Trilhapé
#
# Copyright (c) 2010 Eduardo Pereira Habkost <ehabkost@raisama.net>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.



import sys, subprocess, re

import logging
logger = logging.getLogger('trilhape.planilha')
dbg = logger.debug


FORMFEED ='\x0c'
PASSO = 1.4

class O:
    pass

def pr(s, *args):
    if args:
        s = s % args
    s = s.encode('utf-8')
    print s

class Group:
    def find_width(self):
        width = max([len(l) for l in self.lines])
        for i,l in enumerate(self.lines):
            self.lines[i] = l.ljust(width+3)
        self.width = width

    def can_divide(self, end):
        """Check if the colun at 'end' is filled with spaces"""
        if end >= self.width:
            return True

        for l in self.lines:
            if l[end] <> ' ':
                return False
        return True

    def find_page_limits(self):
        previous = 0
        for p in self.pages:
            ok = False
            for n in (5,6,4,7):
                end = p.min_right+n
                if self.can_divide(end):
                    ok = True

            if not ok:
                raise Exception("I don't know where is the right margin of page %s (%d?)" % (p.number, end))

            p.left = previous
            p.right = end
            previous = end

        for p in self.pages:
            p.lines = [l[p.left:p.right] for l in self.lines]

CUR_VEL = None

class Page:
    def __init__(self, g):
        self.group = g
        self.col_limits = [0]
        self.sidenotes = {}

    @property
    def width(self):
        return self.right-self.left

    def col_lines(self, col):
        limits = self.col_limits[:]
        limits.append(self.width)

        start = self.col_limits[col]
        end = self.col_limits[col+1]
        for l in self.sheet_lines:
            yield l[start:end]

    def add_sidenote(self, i, note):
        dbg('page %s. sidenote %d: %s', self.number, i, note)
        self.sidenotes.setdefault(i, []).append(note)

    def add_sheet_sidenote(self, i, note):
        #XXX: this is a bit fragile, but it should work:
        offset = len(self.lines)-len(self.sheet_lines)

        self.add_sidenote(i+offset, note)

    def parse_sheet(self):
        global CUR_VEL
        self.sheet_lines = self.lines[:]

        def match(pat):
            m = re.search(pat, self.sheet_lines[0])
            if m:
                dbg('match: %r %r', m, self.sheet_lines[0])
                return m,self.sheet_lines.pop(0)

        def skip(pat):
            while match(pat):
                pass

        def skip_blank():
            skip(u'^ +$')


        skip_blank()
        skip(u'^ *TREKKERS *$')
        skip_blank()
        skip(u'^ *TRILHA PÉ AVENTURA *$')
        skip_blank()

        l = match(u'^ *(Distância) +(Referência) +(Observações) *$')
        if l is None:
            raise Exception("Cabeçalho da tabela nao encontrado, pag. %s" % (self.number))
        m,line = l
        skip_blank()

        # add a column limit for ths first column:
        self.col_limits.append(m.end(1)+1)


        state = O()

        state.cur_relative = None
        state.cur_time = None
        state.cur_abs = None
        state.wait_neutro = False

        for i,l in enumerate(self.col_lines(0)):
            if state.cur_abs == 0 and state.cur_time is None:
                # exception: cur_time is implicit if cur_abs is 0
                if state.cur_time is None:
                    state.cur_time = 0

            if state.cur_relative is not None and state.cur_time is not None and state.cur_abs is not None:
                yield i,state.cur_relative,state.cur_time,state.cur_abs
                state.cur_time = None
                state.cur_relative = None
                state.cur_abs = None
                state.wait_neutro = False

            full_line = self.sheet_lines[i]
            dbg('col: %r', l)
            dbg('full line: %r', full_line)

            if state.wait_neutro:
                m = re.search(u'([0-9]{2}):([0-9]{2}):([0-9]{2})', full_line)
                if m:
                    h,m,s = [int(s) for s in m.groups()]
                    t = h*3600+m*60+s
                    # neutro == trecho de 0 metros com tempo percorrido
                    yield i,0,t,0
                    state.wait_neutro = False
                    continue

            if state.cur_relative is None:
                m = re.search('^ *([0-9]{3}) *$', l)
                if m:
                    dbg('got state.cur_rel')
                    state.cur_relative = int(m.group(1))
                    continue

            if state.cur_time is None:
                m = re.search('^ *([0-9]{2}):([0-9]{2}):([0-9]{2}) *$', l)
                if m:
                    h,m,s = [int(s) for s in m.groups()]
                    assert 0 <= h
                    assert 0 <= m < 60
                    assert 0 <= s < 60
                    dbg('got state.cur_time')
                    state.cur_time = h*3600+m*60+s
                    continue

            if state.cur_relative is not None and (state.cur_time is not None or state.cur_relative == 0) and state.cur_abs is None:
                m = re.search('^ *([0-9]{3}) *$', l)
                if m:
                    state.cur_abs = int(m.group(1))
                    dbg('got state.cur_abs')
                    continue

            m = re.search(u'Velocidade Média *([0-9]+) ', full_line)
            if m:
                vel = int(m.group(1))
                steps_min = float(vel)/PASSO
                self.add_sidenote(i, '%.1f passos/min (%.1f BPM)' % (steps_min, steps_min*2))
                CUR_VEL = vel

            if re.search('^ *TRECHO +[0-9]+ *$', full_line):
                # início de trecho: reseta abs
                yield i,0,None,0
                continue

            if re.search('^ *NEUTRALIZADO DE ', full_line):
                state.wait_neutro = True
                continue

            if re.search(u'^ *QUANDO +SEU +CRONÔMETRO', full_line):
                continue

            if re.search(u'DESLOCAMENTO', full_line):
                continue

            if re.search(u'PINUS COM FITAS', full_line):
                continue

            m = re.search('^ *$', l)
            if not m:
                raise Exception("unexpected line: %r" % (l))


    def show(self):
        pr('+%s+' % ('-'*self.width))
        for i,l in enumerate(self.lines):
            notes = ''
            if i in self.sidenotes:
                notes = ' %s' % (' / '.join(self.sidenotes[i]))
            pr('|%s|%s' % (l, notes))
        pr('+%s+' % ('-'*self.width))

def split_groups(lines):
    re_pag = re.compile(u'Página +([A-Z]*)([0-9]+)', re.UNICODE)

    groups = []
    cur = []
    def newpage(matches):
        g = Group()
        g.lines = cur[:]
        g.pages = []
        for m in matches:
            p = Page(g)
            p.min_right = m.end()
            p.number = '%s%s' % (m.group(1), m.group(2))
            g.pages.append(p)


        groups.append(g)

        cur[:] = []

    lastletter = None
    lastpage = 0
    for l in lines:
        # expect to find a form feed char after each page:
        if len(cur) == 0 and len(groups) > 0:
            assert l.startswith(FORMFEED)
            l = l.replace(FORMFEED, '')

        cur.append(l)
        matches = list(re_pag.finditer(l))
        texts = [m.group(0) for m in matches]
        if matches:
            dbg('%r', texts)

        if len(matches) < 2:
            continue

        if len(matches) > 3:
            raise Exception('unexpected matches: %r' % (texts))

        letter = matches[0].group(1)
        pag = int(matches[0].group(2))
        dbg('%r %r', letter, pag)
        dbg('last: %r %r', lastletter, lastpage)
        if (letter <> lastletter and pag == 1) or \
           (letter == lastletter and pag == lastpage+1):
           newpage(matches)
        else:
            raise Exception('unexpected matches: %r. %r %r' % (texts, letter, pag))

        lastletter = matches[-1].group(1)
        lastpage = int(matches[-1].group(2))

    return groups


def _parse_pages(pages):
    for p in pages:
        if p.number.startswith('A'):
            continue
        for i in p.parse_sheet():
            dbg('sheet item: %r', i)
            yield p,i

def msec_to_mmin(v):
    return v*60

def parse_pages(pages):
    prev_time = 0
    prev_abs = 0

    for p,(i,cur_relative,cur_time,cur_abs) in _parse_pages(pages):
        if cur_time is None:
            # None means there's no time info
            cur_time = prev_time

        # cur_abs == 0 means it was just reset
        if cur_abs <> 0 and cur_abs <> prev_abs+cur_relative:
            logger.error("cur_abs doesn't match prev_abs + cur_relative (%d <> %d)" % (cur_abs, prev_abs+cur_relative))

        t_delta = cur_time-prev_time
        assert t_delta >= 0
        if t_delta == 0:
            assert cur_relative == 0

        if t_delta > 0:
            min_speed = msec_to_mmin((cur_relative-0.5)/(t_delta+0.5))
            max_speed = msec_to_mmin((cur_relative+0.5)/(t_delta-0.5))
            speed = msec_to_mmin(float(cur_relative)/t_delta)

        if cur_relative > 0 and t_delta > 0:
            note = 'velocidade: %.1f m/min (%.1f ~ %.1f)' % (speed, min_speed, max_speed)
            if CUR_VEL < min_speed or CUR_VEL > max_speed:
                note += ' *** DIFERENTE DO TRECHO'
            p.add_sheet_sidenote(i-2, note)

        if cur_relative > 0:
            p.add_sheet_sidenote(i-1, 'passos: %.1f' % (float(cur_relative)/PASSO))

        prev_abs = cur_abs
        prev_time = cur_time


def main(argv):
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    fname = argv[0]

    proc = subprocess.Popen(['pdftotext', '-layout', fname, '-'], stdout=subprocess.PIPE)
    lines = proc.stdout.readlines()
    proc.wait()
    if proc.returncode <> 0:
        raise Exception('pdftotext retornou erro!')

    lines = [l.rstrip('\n') for l in lines]
    lines = [unicode(l, 'utf-8') for l in lines]
    groups = list(split_groups(lines))

    dbg('%d groups found', len(groups))
    for g in groups:
        g.find_width()
        g.find_page_limits()

    pages = []
    for g in groups:
        for p in g.pages:
            pages.append(p)

    parse_pages(pages)
    for p in pages:
        p.show()



if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
