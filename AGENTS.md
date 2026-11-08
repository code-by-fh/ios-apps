# Public iOS app catalog

- This repository hosts a public SideStore/AltStore JSON catalog. It does not host private application source code or sign apps.
- Add app feed URLs to apps.json using scripts/register_app.py. Public HTTPS URLs are required even for closed-source apps.
- Use only the Python standard library. Run python -m unittest discover -s scripts -p test_*.py after relevant changes.
- Build with python scripts/build_catalog.py --config apps.json --output altstore-source.json. Publication is atomic; never replace a good catalog with partial results from failed sources.
- Preserve app permissions and complete version history. Reject duplicate bundle identifiers and unexpected configured identities.
- Never store Apple credentials, personal GitHub tokens or private repository URLs with embedded credentials in the registry.
- The workflow updates the catalog on main pushes, manual dispatch and a schedule. PRs run tests but cannot publish.
- The MIT license covers these catalog tools, not the proprietary apps linked in the catalog.
