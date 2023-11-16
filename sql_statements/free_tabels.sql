SELECT t.tischnummer, t.anzahlPlaetze
FROM tische t LEFT JOIN reservierungen r
ON t.tischnummer = r.tischnummer
AND r.zeitpunkt = ?
AND r.storniert = "False"
WHERE r.tischnummer IS NULL