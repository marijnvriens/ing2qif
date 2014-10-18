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

    def _memo_geldautomaat(self, mededelingen, omschrijving):
        if omschrijving.startswith('ING>') or \
                omschrijving.startswith('ING BANK>') or \
                omschrijving.startswith('OPL. CHIPKNIP'):
            memo = omschrijving
        else:
            memo = mededelingen[:32]
        return memo

    def _memo_incasso(self, mededelingen, omschrijving):
        if omschrijving.startswith('SEPA Incasso') or mededelingen.startswith('SEPA Incasso'):
            try:
                s = mededelingen.index('Naam: ')+6
            except:
                raise Exception(mededelingen, omschrijving)
            e = mededelingen.index('Kenmerk: ')
            return  mededelingen[s:e]

    def _memo_internetbankieren(self, mededelingen, omschrijving):
        try:
            s = mededelingen.index('Naam: ')+6
            if "Omschrijving:" in mededelingen:
                e = mededelingen.index('Omschrijving: ')
            else:
                e = mededelingen.index('IBAN: ')
            return  mededelingen[s:e]
        except ValueError:
            return None

    def _memo_diversen(self, mededelingen, omschrijving):
        return mededelingen[:64]

    def _memo_verzamelbetaling(self, mededelingen, omschrijving):
        if 'Naam: ' in mededelingen:
            s = mededelingen.index('Naam: ')+6
            e = mededelingen.index('Kenmerk: ')
            return  mededelingen[s:e]

    def _memo(self):
        """
        Decide what the memo field should be. Try to keep it as sane as possible. If unknown type, include all data.
        :return: the memo field.
        """
        mutatie_soort = self._entry['MutatieSoort']
        mededelingen = self._entry['Mededelingen']
        omschrijving = self._entry['Naam / Omschrijving']

        memo = None
        try:
            memo_method = { # Depending on the mutatie_soort, switch memo generation method.
                'Diversen': self._memo_diversen,
                'Betaalautomaat': self._memo_geldautomaat,
                'Geldautomaat': self._memo_geldautomaat,
                'Incasso': self._memo_incasso,
                'Internetbankieren': self._memo_internetbankieren,
                'Overschrijving': self._memo_internetbankieren,
                'Verzamelbetaling': self._memo_verzamelbetaling,
            }[mutatie_soort]
            memo = memo_method(mededelingen, omschrijving)
        except KeyError:
            pass
        finally:
            if memo is None:
                # The default memo value. All the text.
                memo = "%s %s" % (self._entry['Mededelingen'], self._entry['Naam / Omschrijving'])
        if self._entry_type():
            return "%s %s" % (self._entry_type(), memo)
        return memo.strip()


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
    c = 0
    for entry in CsvEntries(filedescriptor):
        qif.addEntry(entry)
#        if c > 10:
#            break
        c += 1
    print qif.serialize()

if __name__ == '__main__':
    fn = sys.argv[1]
    fd = open(fn, 'rb')
    main(fd)
