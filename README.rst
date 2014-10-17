Convert ING banking statements into QIF to import into Gnucash
==============================================================

Goal:
-----

Make it easy to keep GnuCash up to date. Some transaction details are lost to make matching work better.
This may or may not be acceptable for you.

Usage:
------

 $ python ing2qif.py statements.csv > statements.qif

Note: This was designed around statements from ING in The Netherlands.
Note 2: Other then suffering the ING statement format, there is no relation with ING

Licence:
--------

The GNU General Public License, version 3 or any later version
https://www.gnu.org/licenses/gpl-3.0-standalone.html