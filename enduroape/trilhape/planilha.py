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



import sys, subprocess, re, optparse
from Cheetah.Template import Template

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

def format_time(t):
    t_sec = t
    sec = t%60
    t_sec -= sec
    t_min = int(t_sec/60)
    min = t_min%60
    t_min -= min
    t_hour = int(t_min/60)
    return '%02d:%02d:%02d' % (t_hour, min, sec)

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
            #dbg("l[%d]: %r", end, l[end])
            if l[end] <> ' ':
                return False
        return True

    def find_page_limits(self):
        previous = 0
        for p in self.pages:
            ok = False
            for n in (5,6,4,7,3,8,2,9):
                end = p.min_right+n
                if self.can_divide(end):
                    ok = True
                    break

            if not ok:
                raise Exception("I don't know where is the right margin of page %s (%d?)" % (p.number, end))

            dbg("page columns: %d:%d", previous, end)
            p.left = previous
            p.right = end
            previous = end

        for p in self.pages:
            p.lines = [l[p.left:p.right] for l in self.lines]

class CircuitoItem:
    """Um item no circuito (não necessariamente presente na planilha"""
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def type(self):
        return self.__class__.__name__.lower()

    def is_a(self, t):
        """Shortcut for checking the item class"""
        return self.type.lower() == str(t).lower()

class PageItem(CircuitoItem):
    """Um item na planilha"""
    def __init__(self, page, sheet_line, **kwargs):
        self.page = page
        self.sheet_line = sheet_line
        self.__dict__.update(kwargs)

    def __repr__(self):
        return '<%s: %r>' % (self.__class__, self.__dict__)

    def add_sidenote(self, msg, offset=0):
        self.page.add_sheet_sidenote(self.sheet_line+offset, msg)

# propriedades comuns:
# - sheet_abs_dist - distância absoluta mostrada na planilha (não confiável)
# - rel_dist: distância relativa desde o item anterior
# - abs_time: tempo absoluto
# - ref_index: número (inteiro) da referência (e.g. 1, 2, 3, 42), válido
#   apenas para referências reais (Referencia ou Neutro)
# - ref_id: identificação (string) da referência (e.g. "1", "2", "2.1", "2.2").
#   válido para referências da planilha e parciais (Referencia, Neutro, Parcial)
# - rel_passos: rel_dist convertido para passos

class Referencia(PageItem):
    """Referência

    properties: abs_dist, rel_dist, abs_time, rel_passos, ref_index, ref_id
    """
    @property
    def ref_id(self):
        return str(self.ref_index)

class Parcial(CircuitoItem):
    """Uma parcial

    properties: abs_dist, rel_dist, abs_time, rel_passos, ref_id
    """
    @property
    def ref_id(self):
        return '%d.%d' % (self.ref_before.ref_index, self.parcial_index)

class Neutro(PageItem):
    """Neutro

    properties: abs_time, rel_dist(==0), ref_index, ref_id
    """
    pass
    @property
    def ref_id(self):
        return str(self.ref_index)

class NovoTrecho(PageItem):
    """Novo trecho do circuito

    properties: number, speed
    """
    pass

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
        """Returns an iterator on the items on the sheet page
        """

        self.sheet_lines = self.lines[:]

        def match(pat):
            dbg("match: %r. next line: %r", pat, self.sheet_lines[0])
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
            raise Exception("Cabecalho da tabela nao encontrado, pag. %r" % (self.number))
        m,line = l
        skip_blank()

        # add a column limit for ths first column:
        self.col_limits.append(m.end(1)+1)


        state = O()

        state.cur_relative = None
        state.cur_time = None
        state.cur_abs = None
        state.wait_neutro = False
        state.wait_speed = False
        state.num_trecho = None
        state.last_ref_data_line = None

        def foo():
            dbg("bar")

        def check_referencia():
            """Verifica se há nova referência pronta para ser enviada"""
            #dbg("check_ref: cur_abs: %r, cur_rel: %r, cur_time: %r", state.cur_abs, state.cur_relative, state.cur_time)

            if state.cur_abs == 0 and state.cur_time is None:
                # exception: cur_time is implicit if cur_abs is 0
                state.cur_time = 0

            if state.cur_relative is not None and state.cur_time is not None and state.cur_abs is not None:
                dbg("got new reference")
                # i-1 because the item ended on the previous line
                r = Referencia(self, state.last_ref_data_line, rel_dist=state.cur_relative, abs_time=state.cur_time, sheet_abs_dist=state.cur_abs)
                state.cur_time = None
                state.cur_relative = None
                state.cur_abs = None
                state.wait_neutro = False
                return r

        for i,l in enumerate(self.col_lines(0)):
            r = check_referencia()
            if r: yield r

            full_line = self.sheet_lines[i]
            dbg('col: %r', l)
            dbg('full line: %r', full_line)

            if state.wait_neutro:
                m = re.search(u'([0-9]{2}):([0-9]{2}):([0-9]{2})', full_line)
                if m:
                    h,m,s = [int(s) for s in m.groups()]
                    t = h*3600+m*60+s
                    yield Neutro(self, i, abs_time=t)
                    state.wait_neutro = False
                    continue

            if state.cur_relative is None:
                m = re.search('^ *([0-9]{3}) *$', l)
                if m:
                    dbg('got state.cur_rel')
                    state.cur_relative = int(m.group(1))
                    state.last_ref_data_line = i
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
                    state.last_ref_data_line = i
                    continue

            if state.cur_relative is not None and (state.cur_time is not None or state.cur_relative == 0) and state.cur_abs is None:
                m = re.search('^ *([0-9]{3}) *$', l)
                if m:
                    state.cur_abs = int(m.group(1))
                    state.last_ref_data_line = i
                    dbg('got state.cur_abs')
                    continue

            m = re.search('^ *TRECHO +([0-9]+) *$', full_line)
            if m:
                # início de trecho: reseta abs
                state.num_trecho = int(m.group(1))
                state.wait_speed = True
                continue

            m = re.search(u'Velocidade Média *([0-9]+) ', full_line)
            if m:
                assert state.wait_speed
                vel = int(m.group(1))
                yield NovoTrecho(self, i, number=state.num_trecho, speed=vel)
                state.wait_speed = False

            if re.search('^ *NEUTRALIZADO DE ', full_line):
                state.wait_neutro = True
                continue

            if re.search(u' *QUANDO +SEU +CRONÔMETRO', full_line, re.UNICODE):
                continue

            if re.search(u'DESLOCAMENTO', full_line):
                continue

            if re.search(u'PINUS COM FITAS', full_line):
                continue

            if re.search(u'^ *A EQUIPE TEM [0-9]+ MINUTOS', full_line):
                continue

            if re.search(u'^ *SUBIDA. TRANQUILAMENTE COM CUIDADO', full_line):
                continue

            if re.search(u'^ *COMO CHEGAR (NO|AO|A|NA) ', full_line):
                # fim da planilha em várias provas => instruções como chegar
                break

            if re.search(u'^ *NO SITE DO CLUBE', full_line):
                # fim da planilha (05/2010)
                break

            m = re.search('^ *$', l)
            if not m:
                logger.warn('Page %s, line %d: unexpected line: %r', self.number, i, full_line)
                #raise Exception("unexpected line (%d): %r, %r" % (i, l, full_line))

        r = check_referencia()
        if r: yield r


    def show(self, opts):
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
        dbg("line: %r", l)
        # expect to find a form feed char after each page:
        if len(cur) == 0 and len(groups) > 0:
            assert l.startswith(FORMFEED)
            l = l.replace(FORMFEED, '')

        cur.append(l)
        matches = list(re_pag.finditer(l))
        texts = [m.group(0) for m in matches]
        if not matches:
            continue

        dbg('%r', texts)

        if len(matches) > 3:
            raise Exception('unexpected matches: %r' % (texts))

        letter = matches[0].group(1)
        pag = int(matches[0].group(2))
        dbg('letter: %r. pag: %r', letter, pag)
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
            # A1, A2, A3: instruction pages
            continue
        for i in p.parse_sheet():
            dbg('sheet item: %r', i)
            yield i

def msec_to_mmin(v):
    return v*60

class CircuitoState:
    """Keep track of the current state of sheet parsing"""
    def __init__(self, orig=None):
        if orig is not None:
            # copy data
            self.__dict__.update(orig.__dict__)
            return

        self.abs_dist = 0
        self.abs_time = 0
        self.prev_abs_time = None
        self.trecho_dist = 0
        self.trecho_time = 0

        # last_ref: última Referencia ou Neutro
        self.last_ref = None
        self.last_ref_index = 0

    @property
    def abs_time_str(self):
        """Formatted abs_time"""
        return format_time(self.abs_time)

    def copy(self):
        return CircuitoState(self)

    def add_dist(self, rel_dist):
        self.trecho_dist += rel_dist
        self.abs_dist += rel_dist

    def add_time(self, rel_time):
        dbg("add_time: %d", rel_time)
        self.trecho_time += rel_time

    def reset_trecho(self):
        self.trecho_time = 0
        self.trecho_dist = 0

    def update_abs_time(self, t):
        self.prev_abs_time = self.abs_time
        self.abs_time = t

        t_delta = self.abs_time - self.prev_abs_time
        assert t_delta >= 0
        assert (t_delta > 0) or (self.prev_abs_time == 0) or (isinstance(self.last_ref, Neutro))
        self.add_time(t_delta)
        return t_delta

    def _new_ref(self, ref):
        # throw away the previous reference so it is not copied
        self.previous_state = None
        # make a copy of current state and store it
        self.previous_state = self.copy()

        t_delta = self.update_abs_time(ref.abs_time)
        ref.rel_time = t_delta

        ref.rel_passos = ref.rel_dist/PASSO

        self.last_ref = ref

    def new_ref(self, ref):
        self.last_ref_index += 1
        ref.ref_index = self.last_ref_index
        self._new_ref(ref)
        ref.add_sidenote("Referencia: %s" % (ref.ref_id), -3)

    def posicoes_parciais(self, passos):
        # algoritmo:
        # - gera 1 parciais de 5, 10, 20, e 30 passos para
        #   pegar 'feeling' da velocidade
        # - gera parciais de MAX_PARCIAL passos até chegar a 30 passos do final
        # - parciais a 30,20,10 e 5 passos do final

        dbg("posicoes_parciais: %d passos", passos)

        MAX_PARCIAL = 10

        if passos < 10:
            return

        lp = 0
        for p in (5, 10, 20, 30):
            if p >= passos/2:
                break
            yield p
            lp = p

        p = lp+MAX_PARCIAL
        while p < passos-30:
            yield p
            lp = p
            p += MAX_PARCIAL

        # arredonda os trechos finais para múltiplos de 5
        redondo = int((passos+2.5)/5)*5

        for mp in (30,20,10,5):
            p = redondo-mp
            dbg("ending: %s", p)
            if p > lp+(mp/2) and p < passos:
                yield p
                lp = p


    def gera_parciais(self):
        prev = self.previous_state
        rel_dist = self.abs_dist-prev.abs_dist
        rel_time = self.abs_time-prev.abs_time
        passos = float(rel_dist)/PASSO

        dbg("gera_parciais: ref %s", self.last_ref.ref_id)

        for i,p in enumerate(self.posicoes_parciais(passos)):
            partial_dist = p*PASSO
            partial_time = rel_time*(float(partial_dist)/rel_dist)
            abs_time = prev.abs_time+partial_time
            abs_dist = prev.abs_dist+partial_dist

            parcial = Parcial(abs_time=abs_time, abs_dist=abs_dist, rel_time=partial_time, rel_dist=partial_dist)
            parcial.ref_before = prev.last_ref
            parcial.ref_after = self.last_ref
            parcial.parcial_index = i+1

            # copy current state and update it according to the partial data
            stcopy = prev.copy()
            stcopy._new_ref(parcial)
            yield stcopy,parcial

def parse_pages(opts, pages):
    """Generate state,item tuples

    'item' is the sheet item we just handled
    'state' contains the current state after handling the item.
    """
    st = CircuitoState()

    # keep track of the abs_dist data from the sheet, but
    # it is reset randomly, so probably it can be ignored
    st.sheet_abs_dist = 0
    st.speed = None
    st.last_trecho_num = 0

    #for p,(i,cur_relative,cur_time,cur_abs) in _parse_pages(pages):
    for item in _parse_pages(pages):
        if isinstance(item, Referencia):
            # update current state based on new data:
            st.new_ref(item)
            st.add_dist(item.rel_dist)

            # a distância absoluta é resetada em pontos aleatórios:

            # cur_abs == 0 means it was just reset
            if item.sheet_abs_dist <> st.sheet_abs_dist + item.rel_dist:
                if item.sheet_abs_dist == item.rel_dist:
                    item.add_sidenote('*** abs_dist reset')
                    st.sheet_abs_dist = 0
                else:
                    logger.error("ref %s: Distance doesn't match prev_abs + rel_dist (%d <> %d+%d)" % (item.ref_id, item.sheet_abs_dist, st.sheet_abs_dist, item.rel_dist))

            st.sheet_abs_dist = item.sheet_abs_dist

            assert item.rel_dist >= 0
            if item.rel_dist == 0 and st.trecho_dist <> 0:
                item.add_sidenote("******** rel_dist reset!")
                logger.warn("ref %s: rel_dist é 0 e não é início de trecho", item.ref_id)

            if item.rel_time:
                min_speed = msec_to_mmin((item.rel_dist-0.5)/(item.rel_time+0.5))
                max_speed = msec_to_mmin((item.rel_dist+0.5)/(item.rel_time-0.5))
                speed = msec_to_mmin(float(item.rel_dist)/item.rel_time)

                if st.speed < min_speed or st.speed > max_speed:
                    note = 'velocidade: %.1f m/min (%.1f ~ %.1f)' % (speed, min_speed, max_speed)
                    note += ' *** DIFERENTE DO TRECHO'
                    item.add_sidenote(note, -2)

            item.add_sidenote('passos: %.1f' % (float(item.rel_dist)/PASSO), -1)

            if opts.parciais:
                for s,p in st.gera_parciais():
                    yield s,p

        elif isinstance(item, Neutro):
            item.rel_dist = 0
            st.new_ref(item)
        elif isinstance(item, NovoTrecho):
            assert item.number == st.last_trecho_num+1
            steps_min = float(item.speed)/PASSO
            item.add_sidenote('%.1f passos/min (%.1f BPM)' % (steps_min, steps_min*2))

            st.speed = item.speed
            st.last_trecho_num = item.number
            st.reset_trecho()
        else:
            raise Exception("Unexpected item class: %r" % (item))

        # copy current state and return it
        s = st.copy()
        dbg("last_ref: %s. abs_dist: %d", s.last_ref_index, s.abs_dist)
        yield s,item


def format_html(items):
    print '''
    <style>
        body {
           font-size: 133%;
           font-family: serif;
           font-weight: normal;
        }

        .tempo {
           font-weight: bold;
        }

        .referencia .passos, .parcial .passos {
            text-decoration: underline;
        }

        .neutro .passos {
            font-weight: bold;
        }

        td {
        }

        table {
            border-collapse: collapse;
        }

        .referencia {
           border-top: 1px solid #CCCCCC;
        }

        .odd_ref {
           background-color: #F0F0F0;
        }

        .passos {
            text-align: right;
        }

        .ref_id {
            text-align: left;
        }

        .trecho td {
            padding-top: 3ex;
        }

        .neutro {
            border-bottom: 1px solid black;
            border-top: 1px dashed black;
        }


    </style>
          '''
    print '<table>'
    colunas = 3
    row = 0
    for state,item in items:
        if isinstance(item, NovoTrecho):
            print '<tr class="trecho"><td colspan="%d">TRECHO <strong>%s</strong> (%d m/s)</td></tr>' % (colunas, item.number, item.speed)
        elif isinstance(item, Referencia) or isinstance(item, Parcial) or isinstance(item, Neutro):
            row += 1

            classes=[]
            if isinstance(item, Referencia) or isinstance(item, Parcial):
                if isinstance(item, Referencia):
                    ref = item
                elif isinstance(item, Parcial):
                    ref = item.ref_before

                if ref.ref_index%2==0:
                    classes.append("even_ref")
                else:
                    classes.append("odd_ref")

            if isinstance(item, Referencia):
                classes.append('referencia')
            elif isinstance(item, Parcial):
                classes.append("parcial")
            elif isinstance(item, Neutro):
                classes.append("neutro")

            if row%2==0:
                classes.append('even_row')
            else:
                classes.append('odd_row')

            if isinstance(item, Neutro):
                spassos = 'N'
            else:
                spassos = '%.1f' % (item.rel_passos)

            classes = ' '.join(classes)
            print '<tr class="%s">' % (classes)
            print '<td class="ref_id">%s</td>' % (item.ref_id)
            print '<td class="tempo">%s</td>' % (state.abs_time_str)
            print '<td class="passos">%s</td>' % (spassos)
            print '</tr>'
    print '</table>'

def format_text(items):
    for state,item in items:
        if isinstance(item, NovoTrecho):
            print 'TRECHO %s - %d m/s' % (item.number, item.speed)
        elif isinstance(item, Referencia) or isinstance(item, Parcial) or isinstance(item, Neutro):
            print '%-5s %s %5.1f %5d' % (item.ref_id, state.abs_time_str, item.rel_passos, item.rel_dist)

class TemplateNamespace:
    def __init__(self, opts, items):
        self._opts = opts
        self._items = items

    def circuito(self, type=None):
        for s,i in self._items:
            if type and not i.is_a(type):
                continue
            yield s,i

def format_template(opts, items):
    ns = TemplateNamespace(opts, items)
    t = Template(file=opts.template_file, searchList=[ns])
    sys.stdout.write(t.respond())

def main(argv):
    parser = optparse.OptionParser()
    parser.add_option('-P', help=u"Mostrar páginas originais da planilha", action='store_true', dest='show_pages')
    parser.add_option('-p', help=u"Calcular parciais", action='store_true', dest='parciais')
    parser.add_option('-D', help=u"Mostrar mensagens de debug", action='store_true', dest='debug')
    parser.add_option('--html', help=u"Formata saída em HTML", action='store_true', dest='html')
    parser.add_option('-t', help=u"Usar arquivo de template Cheetah", action='store', dest='template_file')

    opts,args = parser.parse_args(argv)

    if len(args) <> 1:
        parser.error("Especifique o caminho do arquivo PDF com a planilha")

    fname = args[0]

    loglevel = logging.WARN
    if opts.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(stream=sys.stderr, level=loglevel)

    proc = subprocess.Popen(['pdftotext', '-enc', 'UTF-8', '-layout', fname, '-'], stdout=subprocess.PIPE)
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

    items = list(parse_pages(opts, pages))

    if opts.html:
        format_html(items)
    elif opts.template_file:
        format_template(opts, items)
    else:
        format_text(items)

    if opts.show_pages:
        for p in pages:
            p.show(opts)



if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# vim: et ts=4 sw=4:
