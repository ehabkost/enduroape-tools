#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, re, sys, datetime, urlparse, hashlib

import PyRSS2Gen

import logging
logger = logging.getLogger('trilhape.rss')
dbg = logger.debug


#logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)


URL = 'http://www.trilhape.com.br/noticias.php'
ENCODING = 'iso-8859-1'

page_content_re = re.compile(r'<td width="680" .*?>(.*)<td width="10".*?>', re.MULTILINE|re.DOTALL)

first_news_re = re.compile(r"<div class='style4'>(.*?)</div>.*<b>Publicado em: *</b>([0-9]{2}/[0-9]{2}/[0-9]{4})</div>.*<div class='textonoticia'.*?>(.*)<img src=.images/pontinhos.png..*?>", re.MULTILINE|re.DOTALL)

other_news_re = re.compile(r"<div class='style5'><b>(../../....)</b>.*?<div class='textonoticia2'><a href='(.*?)'>(.*?)</a></div>", re.MULTILINE|re.DOTALL)

def parse_date(s):
    d,m,y = s.split('/')
    return datetime.datetime(int(y), int(m), int(d))

def u(s):
    return unicode(s, ENCODING)

def hash_content(s):
    h = hashlib.sha1()
    h.update(s)
    return h.hexdigest()

class Item:
    def __repr__(self):
        return '<Item: %r>' % (self.__dict__)

def gen_news_items():
    s = urllib.urlopen(URL).read()

    content = page_content_re.search(s).group(1)
    dbg('content: %r', content)

    first = first_news_re.search(content)
    dbg('first: %r', first.groups())

    i = Item()
    i.date = parse_date(first.group(2))
    i.title = u(first.group(1))
    i.content = u(first.group(3))
    # I hope this works...
    i.url = URL

    q = {'last_date':str(i.date), 'last_title':i.title, 'content_hash':hash_content(i.content.encode('utf-8'))}
    qs = urllib.urlencode(q)
    i.guid = '%s?%s' % (URL, qs)
    yield i

    for o in other_news_re.finditer(content):
        dbg('other: %r', o.groups())
        i = Item()
        i.date = parse_date(o.group(1))
        i.title = u(o.group(3))
        i.content = ''
        i.url = urlparse.urljoin(URL, o.group(2))
        i.guid = i.url
        yield i

def create_feed():
    items = list(gen_news_items())

    return PyRSS2Gen.RSS2(
        title = u'Notícias Trilhapé',
        link = URL,
        description = u"Feed para as notícias do site do Trilhapé",

        items = [
            PyRSS2Gen.RSSItem(
                title = i.title,
                link = i.url,
                guid = PyRSS2Gen.Guid(i.guid),
                pubDate = i.date)
            for i in items])


f = create_feed()
f.write_xml(sys.stdout, encoding='utf-8')
