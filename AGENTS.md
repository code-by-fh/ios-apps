# Public iOS app catalog

- This repository hosts a public SideStore/AltStore JSON catalog. It does not host private application source code or sign apps.
- Add app feed URLs to apps.json using scripts/register_app.py. Public HTTPS URLs are required even for closed-source apps.
- Use only the Python standard library. Run python -m unittest discover -s scripts -p test_*.py after relevant changes.
- Build with python scripts/build_catalog.py --config apps.json --output altstore-source.json. Publication is atomic; never replace a good catalog with partial results from failed sources.
- Preserve app permissions and complete version history. Reject duplicate bundle identifiers and unexpected configured identities.
- Never store Apple credentials, personal GitHub tokens or private repository URLs with embedded credentials in the registry.
- The catalog is published ONLY by a manual workflow_dispatch run on main. Pushes and PRs run checks only. Never add a schedule or automatic publication trigger without an explicit user request.
- The MIT license covers these catalog tools, not the proprietary apps linked in the catalog.

## Manual refresh lifecycle

- `.github/workflows/refresh-catalog.yml` has no schedule. The user's explicit preference is manual catalog publication only.
- Pushes to main and pull requests run tests, but the refresh job must require BOTH `github.event_name == 'workflow_dispatch'` AND `github.ref == 'refs/heads/main'`.
- To update on GitHub: Actions > Refresh app catalog > Run workflow > main > Run workflow.
- CLI: `gh workflow run refresh-catalog.yml --repo code-by-fh/ios-apps --ref main`. Check the resulting Actions run for success.
- The workflow runs on GitHub-hosted runners; the user's Windows PC and AI agent may be offline after requesting it.
- A manual run first executes tests. The refresh job reads all enabled public source URLs in apps.json, validates metadata, versions, permissions and unique bundle IDs, then atomically generates altstore-source.json.
- Commit and push the generated JSON only if it changed. No empty commits. The workflow does not rebuild or sign any IPA.
- Failed fetches, invalid metadata or duplicate bundle IDs fail the run and leave the published catalog unchanged. Fix the source or disable its registry entry, commit and push, then manually rerun the workflow.
- Publishing a new version in an app repository does not update this catalog automatically. Request a manual catalog refresh after the public app source is ready.

## Registering open- and closed-source apps

- Register using `python scripts/register_app.py --repository owner/app-releases --license open-source` or `--license closed-source`. Commit and push apps.json, THEN manually start the catalog workflow.
- The license label is registry metadata; it changes neither app permissions nor app licensing.
- Closed-source app code may stay private. Its distribution JSON, icon and IPA must be public HTTPS downloads; the catalog never needs private-repository credentials.
- SideStore refreshes its own source list separately. A completed catalog workflow does not force an immediate source refresh or app installation on the iPhone.

## English text policy

- Keep all authored repository text in English, including current and future README files, documentation, UI text, comments, messages, script output, tests, metadata, configuration descriptions, commit messages and agent instructions.
- Preserve technical identifiers, URLs, product names, user names and external data. Do not translate or manually edit generated altstore-source.json; publish configuration changes through the manual catalog workflow only.
