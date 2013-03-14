#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from colorama import Fore, Style
import dateutil.tz
import logbook

class ColoringFormatter(logbook.StringFormatter):
    color_table = {
        logbook.CRITICAL: Fore.RED + Style.BRIGHT,
        logbook.ERROR: Fore.RED,
        logbook.WARNING: Fore.YELLOW,
        logbook.INFO: Fore.GREEN + Style.DIM,
        logbook.DEBUG: Style.DIM,
        logbook.NOTSET: Fore.GREEN,
    }

    def format_record(self, record, handler):
        out = super(ColoringFormatter, self).format_record(record, handler)

        return self.color_table[record.level] + out\
               + Fore.RESET + Style.RESET_ALL

class ColoringLog(logbook.StderrHandler):
    formatter_class = ColoringFormatter
    default_format_string = (
            u'[{record.local_time:%H:%M:%S}] '
        u'{record.channel}: {record.message}'
    )
    _prev_date = None

    def emit(self, record):
        utc_time = record.time.replace(tzinfo=dateutil.tz.tzutc())
        record.local_time = utc_time.astimezone(dateutil.tz.tzlocal())
        if not self._prev_date or record.local_time.date() != self._prev_date:
            self.lock.acquire()
            try:
                self.write('[{record.local_time:%Y-%M-%D}]\n'.format(record=record))
            finally:
                self.lock.release()
        super(ColoringLog, self).emit(record)

        self._prev_date = record.local_time.date()


if __name__ == '__main__':
    # small example
    log = logbook.Logger('sample.log')

    hdl = ColoringLog()

    hdl.push_application()

    log.debug('this is a debug message')
    log.warning('this is a warning message')
    log.info('this is an info message')
    log.error('this is an error message')
    log.critical('this is a critical message')
