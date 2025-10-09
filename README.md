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
- Kategorie (Wasser, Workshop, ...)# Initiale Verteilung
Wir benötigen folgende Informationen:
## Slots
- Sperrzeiten für alle ??? (Shows)
- Sperrzeiten für einzelne Abteilungen ??? (Duschen)
	- Wer organisiert Duschezeiten? LOG? Sollen wir einplanen?

## Blöcke
### Infos
- Name (PKey)
- Voller Name
- Kapazität TN
- Ort
- Kategorie (Wasser, Workshop, ...)
- berechtigte Stufen
- Durchführungszeiten
### Regeln
- Wasseraktivitäten / Workshops: 1 pro Woche?
- Duschen == Wasseraktivität ???

## Abteilungen
### Infos
- Name (PKey)
- Voller Name
- Kontakt ??? (für automatischen Versand später)
- Anzahl TN
- Stufe

- Anwesenheit an Tagen
- Wanderung gewünscht (1d, 2d, ...)
- Frei an spezifischen Tagen ???
- Frei in spezifischen Slots ???
- Anzahl Blöcke gewünscht ???
- Prioliste (siehe unten)

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
- ca 15-20 Prios absteigend angeben:
	- 1. Prio: Block X
	- 2. Prio: Block Y
	- ....
	- 15. Prio: Block Z
- Vorteile:
	- sehr genaue Angabe
- Nachteile
	- Unnötig differenziert ("ist jetzt Block A unsere 13. Prio oder 14. Prio?")
	- Lässt uns weniger Freiheiten bei Blockeinteilung

## Fairness
Vorschlag: 
- Score für jede Abteilung anhand von Prios und Zugeteilten Blöcken
- Optimieren für Score von tiefster Abteilung
- Abteilung die am Meisten benachteiligt wird, möglichst viele Prios erhalten. Alle anderen Abteilungen sind besser, und haben nicht zu motzen
- Score Berechnung: Wichtige technische Einzelheiten, kann gerne diskutiert werden, Vorschlag:
$$
s_{N} = \frac{{\sum_{zugeteilte}(5-prio )}}{\sum_{topNprios} (5-prio)}
$$
Das heist die erreichten Blöcke werden normiert anhand der Gewichte-Verteilung ihrer top N Prios. Wenn mehr Blöcke zugeteilt werden als Prios verwendet werden zur Normierung kann auch ein Score über 1 erreicht werden.

Beispiel für top11 prios:
Abteilung 1 hat jeweils 5 mal prio 1, 2, ... 5. Ihre Top11prios (Divisor) sind entsprechend $4(5-1_{p}) + 4(5-2_{p}) + 3 (5-3_{p}) = 34$ 
Abteilung 1 Bekommt: 3x Prio 1, 4x Prio 2 und 4x Prio 3, ergibt:
für Dividend $3(5-1_{p}) + 4 (5-2_{p}) + 4(5-3_{p})= 32$
Score entsprechend: $\frac{32}{34} = 0.94$

Möchtegern schlaue Abteilung 2 hat jeweils 11x prio 1 und sonst prio 5. Ihre Top11prios (Divisor) sind entsprechend $11(5-1_{p})= 44$ 
Abteilung 2 bekommt: 10 Prio 1, sonst nichts:
für Dividend $10(5-1_{p})= 40$
Score entsprechend: $\frac{40}{44} = 0.91$

Gespässige Abteilung 3 gibt nur tiefe prios an: 6x prio3, 6x prio 4, rest prio 5 und bekommt 5x prio3 und 6x prio4:
ergibt $\frac{{5(5-3_{p}) + 6(5-4_{p})}}{6(5-3_{p})+5(5-4_{p})} = \frac{16}{17} = 0.94$ 

Wolffstufeneinheiten sind nur eine Woche da, wir verwenden top5prios zur Normierung:
Prios: 3x prio1, 5x prio, 5x prio3
Bekommt: 2x prio1,  3x prio2
$\frac{2(5-1_{p}) + 3(5-2_{p})}{3(5-1_{p}) + 2(5-2_{p})} = \frac{17}{18} = 0.94$

Scores sind unabhängig von Prioverteilung und Blockanzahl

## Ablauf
Wir sortieren alle Abteilungen nach Score aufsteigend (Am Anfang sind alle 0). Abteilung mit niedringstem Score darf block setzen. Wir wählen einen Block mit hoher Prio, suchen einen Slot der dem Block passt (Belegungen des Blocks werden beachtet), suchen freie und passende Slots der Einheit. Wenn passender slots gefunden bei beiden, setzen den Block und gehen zur nächsten Einheit. Wenn kein passender Slot gefunden, versuchen dasselbe mit anderem Block für dieselbe Einheit. Wenn alle Einheiten einen Block gesetzt haben, sortieren wir wieder nach Score und beginnen von vorne. Abbruchbedingungen sind festzulegen (11 resp 5 Blöcke pro Einheit?)

Duschzeiten und Wanderungen könnten ebenfalls so verteilt werden, oder bereits im vorherein. Dann müssen diese Zeiten einfach gesperrt werden für jeweilige Abteilungen.
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




