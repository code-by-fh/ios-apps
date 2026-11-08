# iOS Apps

A central app catalog for SideStore and AltStore Classic. The catalog combines publicly accessible app sources and supports both open-source and closed-source apps. Distributing an IPA does not require publishing its source code.

After this repository has been published successfully, use this source URL:

```text
https://raw.githubusercontent.com/code-by-fh/ios-apps/main/altstore-source.json
```

In SideStore, open **Sources → + / Add Source** and enter this address. Verify that the URL is publicly reachable after pushing the repository. A locally generated JSON file alone does not demonstrate public availability. Your sideloader handles installation and signing with your own Apple Account.

## Structure

`apps.json` lists the registered sources. Each enabled source supplies its own JSON with app metadata, permissions and version-specific IPA download URLs. The catalog combines this information into `altstore-source.json`. It does not need access to private app repositories, Apple credentials or additional access tokens.

SideStart is the first registered source:

```json
{
  "sources": [
    {
      "url": "https://github.com/code-by-fh/sidestart/releases/latest/download/altstore-source.json",
      "license": "open-source",
      "enabled": true,
      "expectedBundleIdentifiers": ["dev.sidestart.sidestart"]
    }
  ]
}
```

Each app must have a unique bundle identifier. App sources and download URLs must be accessible without signing in. Actions artifacts from private GitHub repositories therefore cannot serve as public download URLs.

## Add an app

If a public release repository already provides `altstore-source.json`, an icon and an IPA:

```powershell
python scripts/register_app.py --repository owner/app-releases --license closed-source
git add apps.json
git commit -m "Register app source"
git push
gh workflow run refresh-catalog.yml --repo code-by-fh/ios-apps --ref main
```

Replace `owner/app-releases` with the actual release repository. For an open-source app, use `--license open-source`. The registration command derives the source URL from the repository name; the source must be attached to its latest GitHub release.

The `open-source` and `closed-source` labels describe the licensing model. They do not change iOS permissions or publish app source code. See [docs/CLOSED_SOURCE.md](docs/CLOSED_SOURCE.md) for the complete process with a private development repository.

## Refresh the catalog

The catalog is updated **only by manually starting its GitHub workflow on `main`**. There is no schedule. Pushes and pull requests run checks without publishing the catalog. New app releases also require a manual refresh before they appear in the combined catalog.

On GitHub: **Actions → Refresh app catalog → Run workflow → Branch main → Run workflow**. Alternatively:

```powershell
gh workflow run refresh-catalog.yml --repo code-by-fh/ios-apps --ref main
```

The workflow reads the registered public sources and uses the repository's `GITHUB_TOKEN` to update the generated JSON on `main`. It creates a commit only when the catalog changes. No additional secrets are required. Your PC can be offline while the GitHub-hosted workflow runs.

If an enabled source is invalid or unavailable, the refresh fails and preserves the last successfully published catalog. Check the Actions run and the affected app source if an update does not appear.

Changes to authored metadata in `apps.json`, including its English description, appear in the generated catalog only after the next successful manual refresh. Do not edit `altstore-source.json` directly to bypass this lifecycle.

## Licensing and installation

This repository's MIT license covers its catalog tools and original code. It **does not license the listed apps or IPA files**. Each app remains subject to its rights holder's terms. A publicly downloadable binary is not confidential, but it can still be proprietary software.

The [SideStore prerequisites](https://docs.sidestore.io/docs/installation/prerequisites) and [free Apple Account limits](https://docs.sidestore.io/docs/faq) still apply. The source format follows the [AltStore documentation](https://faq.altstore.io/developers/make-a-source).

Keep all maintained documentation, comments, configuration descriptions and other authored text in English.
