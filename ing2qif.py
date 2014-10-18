#!/usr/bin/python
# (C) 2014, Marijn Vriens <marijn@metronomo.cl>
# GNU General Public License, version 3 or any later version

# Documents
# https://github.com/Gnucash/gnucash/blob/master/src/import-export/qif-imp/file-format.txt
# https://en.wikipedia.org/wiki/Quicken_Interchange_Format

import sys
import csv
import itertools

class Entry(object):
    """
    I represent one entry.
    """
    def __init__(self, data):
        self._data = data
        self._cleanUp()
    def _cleanUp(self):
        self._data['amount'] = self._data['Bedrag (EUR)'].replace(',', '.')
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
        """
        Add an entry to the list of entries in the statment.
        :param entry: A dictionary where each key is one of the keys of the statement.
        :return: Nothing.
        """
        self._entries.append(QifEntry(entry))

    def serialize(self):
        """
        Turn all the entries into a string
        :return: a string with all the entries.
        """
        data = ["!Type:Bank"]
        for e in self._entries:
#            if len(e._memo()) > 32:
                data.append(e.serialize())
        return "\n".join(data)


class QifEntry(object):
    def __init__(self, entry):
        self._entry = entry
        self._data = []
        self.processing(self._data)

    def processing(self, data):
        data.append("D%s" % self._entry.Datum)
        data.append("T%s" % self._amount_format())
        if self._entry_type():
            data.append('N%s' % self._entry_type())
        data.append("M%s" % self._memo())
        data.append("^")

    def serialize(self):
        """
        Turn the QifEntry into a String.
        :return: a string
        """
        return "\n".join(self._data)

    def _memo(self):
        """
        Decide what the memo field should be. Try to keep it as sane as possible. If unknown type, include all data.
        :return: the memo field.
        """
        mutatie_soort = self._entry['MutatieSoort']
        mededelingen = self._entry['Mededelingen']
        omschrijving = self._entry['Naam / Omschrijving']

        # The default memo value. Basically all text.
        memo = "%s %s" % (self._entry['Mededelingen'], self._entry['Naam / Omschrijving'])

        if mutatie_soort == 'Betaalautomaat':
            memo = mededelingen[:32]
        elif mutatie_soort == 'Geldautomaat':
            if omschrijving.startswith('ING>') or omschrijving.startswith('OPL. CHIPKNIP'):
                memo = omschrijving
            else:
                memo = mededelingen[:32]
        elif mutatie_soort == 'Incasso':
            if omschrijving.startswith('SEPA Incasso'):
                s = mededelingen.index('Naam: ')
                e = mededelingen.index('Kenmerk: ')
                memo = mededelingen[s:e]
        return memo

    def _amount_format(self):
        if self._entry['Af Bij'] == 'Bij':
            return "+" + self._entry['amount']
        else:
            return "-" + self._entry['amount']

    def _entry_type(self):
        """
        Detect the type of entry.
        :return:
        """
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
    qif = QifEntries()
    for entry in CsvEntries(filedescriptor):
        qif.addEntry(entry)
    print qif.serialize()

if __name__ == '__main__':
    fn = sys.argv[1]
    fd = open(fn, 'rb')
    main(fd)
