# Home Assistant catalog

App source lives in `tvrooi/Allotment`; this repository only promotes verified release metadata.
Do not edit generated `flybudget_up/` files by hand. Change the application, publish its release,
then run **Sync Allotment release** (or wait for the hourly check).

Test importer changes with `python3 -m unittest discover -s scripts`. Keep bundle provenance,
checksums, source commit/image digest validation, permission guard and downgrade protection.
Never include production data, tokens, keys or deployment hostnames. Never migrate the installed
local app as part of a catalog update: it has a different app ID and needs a cold backup/restore.
