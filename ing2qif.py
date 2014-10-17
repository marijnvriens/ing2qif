#!/usr/bin/python
# (C) 2014, Marijn Vriens <marijn@metronomo.cl>
# GNU General Public License, version 3 or any later version

import sys
import csv
import itertools

class Entry(object):
    def __init__(self, data):
        self._data = data
        self._cleanUp()
    def _cleanUp(self):
        self._data['amount'] = self._data['Bedrag (EUR)'].replace(',', '.')
        self._data['memo'] = "%s %s" % (self._data['Mededelingen'], self._data['Naam / Omschrijving'])
    def keys(self):
        return self._data.keys()
    def __getattr__(self, item):
        return self._data[item]
    def __getitem__(self, item):
        return self._data[item]


class CsvEntries(object):
    def __init__(self, filedescriptor):
        self._entries = csv.DictReader(filedescriptor)

    def __iter__(self):
        return itertools.imap(Entry, self._entries)


class QifEntries(object):
    def __init__(self):
        self._entries = []

    def addEntry(self, entry):
        self._entries.append(QifEntry(entry))

    def serialize(self):
        data = ["!Type:Bank"]
        for e in self._entries:
            data.append(e.serialize())
        return "\n".join(data)


class QifEntry(object):
    def __init__(self, entry):
        self._entry = entry

    def serialize(self):
        data = []
        data.append("D%s" % self._entry.Datum)
        data.append("T%s" % self._amount_format())
        if self._entry_type():
            data.append('N%s' % self._entry_type())
        data.append("M%s" % self._memo())
        data.append("^")
        return "\n".join(data)

    def _memo(self):
        mutatie_soort = self._entry['MutatieSoort']
        mededelingen = self._entry['Mededelingen']
        omschrijving = self._entry['Naam / Omschrijving']
        memo = self._entry['memo']
        if mutatie_soort == 'Betaalautomaat':
            memo = mededelingen[:32]
        elif mutatie_soort == 'Geldautomaat':
            if omschrijving.startswith('ING>') or omschrijving.startswith('OPL. CHIPKNIP'):
                memo = omschrijving
            else:
                memo = mededelingen[:32]
        #elif mutatie_soort == 'Incasso':
        return memo

    def _amount_format(self):
        if self._entry['Af Bij'] == 'Bij':
            return "+" + self._entry['amount']
        else:
            return "-" + self._entry['amount']

    def _entry_type(self):
        try:
            return {
                'Geldautomaat': "ATM",
                'Internetbankieren': "Transfer",
                'Incasso': 'Transfer',
                'Verzamelbetaling': 'Transfer',
                'Betaalautomaat': "ATM",
                'Storting': 'Deposit',
            }[self._entry['MutatieSoort']]
        except KeyError:
            return None


def main(filedescriptor):
    c = 0
    qif = QifEntries()
    for entry in CsvEntries(filedescriptor):
        if c > 10:
            break
        c += 1
        qif.addEntry(entry)
    print qif.serialize()

if __name__ == '__main__':
    fn = sys.argv[1]
    fd = open(fn, 'rb')
    main(fd)
