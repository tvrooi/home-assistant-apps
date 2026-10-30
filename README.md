# Allotment for Home Assistant

Every dollar gets its plot. Allotment was the FlyBudget Up fork; the app keeps its ID
(`flybudget_up`), so an installed app updates in place.

[Application source and desktop downloads](https://github.com/tvrooi/Allotment) · [Release workflow](https://github.com/tvrooi/Allotment/blob/main/MAINTENANCE.md)

Add this repository in **Settings → Apps → Install app → ⋮ → Repositories**:

```
https://github.com/tvrooi/home-assistant-apps
```

[Add to Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Ftvrooi%2Fhome-assistant-apps)

The app appears after the first successful application release is promoted. Images are prebuilt
for AMD64 and ARM64. The catalog sync checks hourly, or run **Actions → Sync Allotment release**
for an immediate refresh. Home Assistant then offers its normal **Update** button.

Use Allotment's standalone URL or the desktop preview. HA hosts the database and bank connection;
Allotment has its own password. Up sync runs at server startup and via **Sync Now**, not periodically.

## Moving from the manually installed preview

The repository app has a **different ID and data folder** from `local_flybudget_up`. Installing it
creates a new empty budget; it does not move the existing one. Keep the local app running until
you have a verified cold HA backup and a planned restore of its private data, including the encryption
key. Stop the old app before switching the new one to port 3001. Do not uninstall or delete it until
login, transaction/account counts and the bank connection have been verified in the new app.
A JSON export does not include the Up token. See [maintenance/migration notes](https://github.com/tvrooi/Allotment/blob/main/MAINTENANCE.md).

## How updates work

Application source lives only in `tvrooi/Allotment`. A completed release supplies a signed metadata
bundle. This repository verifies its GitHub provenance, exact file checksums, version, source commit
and public container digest before updating `flybudget_up/`. There are no personal access tokens or
cross-repository write credentials. No databases, keys, account details or bank exports belong here.

Allotment is built on FlyBudget. The fork and app are independent community previews under
AGPL-3.0-only, not official FlyBudget, Up Bank or Home Assistant releases. Retain the original license and copyright notices.
