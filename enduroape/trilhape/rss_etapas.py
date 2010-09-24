#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, re, sys, datetime, urlparse, hashlib

import PyRSS2Gen

import logging
logger = logging.getLogger('trilhape.rss_etapas')
dbg = logger.debug


#logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)


URL = 'http://www.trilhape.com.br/etapas.php'
ENCODING = 'iso-8859-1'

page_content_re = re.compile(r'<h1 class="titulo_grande">Calend&aacute;rio das Etapas</h1>(.*?)</table>', re.MULTILINE|re.DOTALL)

items_re = re.compile(r"<tr>(.*?)</tr>", re.MULTILINE|re.DOTALL)
re_td = re.compile(r"</*td.*?>", re.MULTILINE|re.DOTALL)
re_title = re.compile(r"<strong>(.*?)</strong>")

re_empty = re.compile(r'^\s*<td.*?><p.*?>\&nbsp;</p></td>\s*|\s*$', re.DOTALL)

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

    for o in items_re.finditer(content):
        dbg('item: %r', o.groups())

        content = o.group(1)
        if re_empty.match(content):
            continue

        content = re_td.sub('<span>', content)
        title = re_title.search(content).group(1)

        i = Item()
        i.title = u(title)
        i.content = u(content)
        i.url = URL
        i.guid = 'http://http://www.trilhape.com.br/etapas.php?hash='+hash_content(content)
        yield i

def create_feed():
    items = list(gen_news_items())

    return PyRSS2Gen.RSS2(
        title = u'Etapas Trilhapé',
        link = URL,
        description = u"Feed para alterações nas página sobre as etapas Trilhapé",

        items = [
            PyRSS2Gen.RSSItem(
                title = i.title,
                link = i.url,
                guid = PyRSS2Gen.Guid(i.guid, isPermaLink = 0),
                description = i.content)
            for i in items])


f = create_feed()
f.write_xml(sys.stdout, encoding='utf-8')
