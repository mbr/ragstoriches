#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Download(object):
    BUFFER_SIZE=16*1024
    def __init__(self, response):
        self.response = response
        self.on_progress = lambda s,t: None

    def read(self, len=0):
        buf = StringIO()
        self.save_to(buf)
        return buf.getvalue()

    def save_to(self, outfn):
        with open(outfn, 'wb') as out:
            saved = 0
            total = int(r.headers.get('content-length', '0'))

            self.on_progress(saved, total)
            for chunk in r.iter_content(self.BUFFER_SIZE):
                out.write(chunk)
                saved += len(chunk)
                self.on_progress(saved, total)

    def __str__(self):
        return '<Download stream of %s>' % self.response.url
