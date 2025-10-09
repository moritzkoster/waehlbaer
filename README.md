# Initiale Verteilung
## Slots
- Sperrzeiten für alle ??? (Shows)
- Sperrzeiten für einzelne Abteilungen ??? (Duschen)
	- Wer organisiert Duschezeiten? LOG? Sollen wir einplanen?

## Blöcke
### Infos
- Name (PK)
- Voller Name
- Kapazität TN
- Ort
- Kategorie (Wasser, Workshop, ...)
- Stufen
- Durchführungszeiten
### Regeln
- Wasseraktivitäten / Workshops: 1 pro Woche?
- Duschen == Wasseraktivität ???

## Abteilungen
### Infos
- Name (PK)
- Voller Name
- Kontakt ??? (für automatischen Versand später)
- Anzahl TN
- Stufe

### Anforderungen
- Anwesenheit an Tagen
- Wanderung gewünscht (1d, 2d, ...)
- Frei an spezifischen Tagen ???
- Frei in spezifischen Slots ???
- Anzahl Blöcke gewünscht ???

### Prioliste
Vorschlag:
- Jeden Block raten von 1-5: 
	- 1: 1. Prio, möchten wir haben
	- 2: 2. Prio, ...
	- 3: 3. Prio:, ...
	- 4: Nehmen wir im Notfall, Besser als nichts
	- 5: Machen wir nicht, lieber Freizeit als das (wird entsprechend garantiert nicht zugeteilt)
- Empfehlung: ca. 20 Blöcke in Prios 1-3, keine feste limits
- Vorteile:
	- Nicht zu differenziert (nicht alle blöcke zueinander gerated)
	- Läst uns mehr Freiheiten bei Blockeinteilung:
		- Haben 5x 3.Prio zu vergeben, können da m
- Nachteile
	- Einige Abteilungen geben vielleicht zu wenig/keine prios an
		- Lösung: keine Prios:
			- Alles Prio 1,
		- Lösung zu wenig Prios:
			- ???

Vorschlag 2:
- N (ca 15-20) Prios absteigend angeben:
	- 1. Prio: Block X
	- 2. Prio: Block Y
	- ....
	- 15. Prio: Block Z
- Vorteile:
	- sehr genaue angabe
- Nachteile
	- Sehr differenziert ("ist jetz Block A unsere 13. Prio oder 14. Prio?")
	- Lässt uns weniger Freiheiten bei Blockeinteiung

## Fairness
Vorschlag: 
- Score für jede Abteilung anhand von Prios und Zugeteilten Blöcken
- Optimieren für Minimum Score
- Abteilung die am Meisten benachteiligt wird, möglichst viele Prios erhalten. Alle anderen Abteilungen sind besser, und haben nicht zu motzen
- Score berechnung: Wichtige technische Einzelheiten, kann gerne diskutiert werden, Vorschlag

## Output
### Für PROG
- Fettes Excel mit Tab für jede Abteilung und Block:
	- kann von Hand angepasst werden, muss aber immer nachgeführt werden bei Abteilung und Block
- ???
### Für Abteilungen und Blöcke
- Dokument mit zugeteilten Blöcken mit allen Infos (PDF, Word, Excel, was ihr wollt)
- .ics Kalender File
- ???

# Manuelle Anpassung
Annahme: Manuelle Anpassungen kurz vor/Während Lager sind unumgänglich (Blöcke werden abgesagt, Einheiten kommen nicht, was auch immer)

Wie wollt ihr das machen? (Spoiler: Lano hat keine Zeit während Kala)

Idee 1: 
- Händisches anpassen von Excel file auf Drive
	- Vorteile: 
		- Mobile
		- von allen einsehbar und bearbeitbar
		- "stabil" (solange Gdrive online ist)
		- Flexibel (mehre Abteilungen pro Slot, etc)
	- Nachteile: 
		- Braucht viel Disziplin, muss bei Blockprogramm und Abteilungsprogramm gleichzeitig angepasst werden, damit immer übereinstimmt

Idee 2
- Erweiterung von Wählbär mit einem UI
	- Vorteile:
		- Abteilungsprogramm und Blockprogramm werden simultan angepasst
		- Einfacher ersichtlich welche Blöcke verfügbar sind in einem Slot für neue Zuteilung
	- Nachteile:
		- Lokale Software, synchronisieren auf andere Geräte bleibt Handarbeit
		- Eher instabil auf abstürze, Bugs, ...
		- nicht wirklich flexibel
		- Software muss auf jedem Gerät laufen,..

Idee 3: (Lano macht das nicht, müsst ihr selber erbasteln)
- Erweiterung mit Web-App UI
	- Vorteile
		- Abteilungsprogramm und Blockprogramm werden simultan angepasst
		- Einfacher ersichtlich welche Blöcke verfügbar sind in einem Slot für neue Zuteilung
		- von allen einsehbar und bearbeitbar
		- Mobile
	- Nachteile
		- Seeeehr instabil (Serverabstürze, gleichzeitige Bearbeitung von versch. Personen, ...)
		- nicht wirklich flexibel




