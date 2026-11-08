# Register a closed-source app

The central catalog needs a public source JSON file and publicly downloadable IPAs. Your Flutter project, Git history and build scripts can stay in a private repository. Use a separate public release repository for downloads.

```text
Private app repository
        ↓ iOS build on macOS in GitHub Actions
Private Actions artifacts: unsigned IPA
        ↓ explicitly publish download files
Public release repository: IPA + JSON + icon + checksum
        ↓ register the public source URL in apps.json
Central catalog: code-by-fh/ios-apps
        ↓ manually refresh the catalog
SideStore / AltStore Classic
```

## 1. Develop and build privately

Give each app its own bundle identifier, such as `com.yourcompany.myprivateapp`. Build an unsigned **release app for a physical iOS device** in your private app repository. Download the IPA from a successful Actions run and check it before publication. Successful packaging does not replace an installation test on an iPhone.

The IPA includes the distributed app and its embedded resources. Keep secrets out of app code and assets. Closed source code does not make a publicly distributed binary confidential.

## 2. Create a public download repository

Using your existing GitHub CLI authentication:

```powershell
gh auth status
gh repo create owner/my-private-app-releases --public --add-readme
```

Replace `owner` with your GitHub username or organization and choose an available repository name. This creates a new repository specifically for public binary downloads. Your private development repository keeps its existing visibility.

Add a notice explaining the app's actual license, such as a proprietary license specifying the usage rights you permit. Public downloads and catalog registration do not automatically grant an open-source license.

## 3. Publish the IPA and app source

If your private app project uses the prepared `scripts/publish_source.py` publisher, run this command there:

```powershell
python scripts/publish_source.py --repository owner/my-private-app-releases --ipa downloads/my-private-app.ipa
```

The explicit target identifies your public download repository. The publisher uploads the IPA, its generated source JSON, an icon and a checksum. It does not copy project source code or make an existing private repository public. Local GitHub CLI authentication is sufficient; this process needs no additional CI secrets.

The prepared publisher supports a minimal ARM64 app without additional app extensions or embedded provisioning profiles. It reads the app name from the IPA's `CFBundleDisplayName`; the template sets that name through the app configuration when generating platform files. The description and plus icon are template defaults that you can customize. Bundle identifier, version, build number, minimum iOS version, package size and permissions also come from the actual IPA. Review additional native capabilities before extending the template.

The app source must then be available without authentication:

```text
https://github.com/owner/my-private-app-releases/releases/latest/download/altstore-source.json
```

Also check the IPA download and icon linked by this JSON without signing in to GitHub. The publisher checks public URLs after upload; only successful completion confirms that verification.

## 4. Register it in the central catalog

In your local checkout of `code-by-fh/ios-apps`:

```powershell
python scripts/register_app.py --repository owner/my-private-app-releases --license closed-source
git add apps.json
git commit -m "Register closed-source app"
git push
gh workflow run refresh-catalog.yml --repo code-by-fh/ios-apps --ref main
```

Registration adds the public app source URL and its license label. The catalog workflow reads metadata from this public endpoint without accessing the private app project.

## 5. Publish updates

Build and download a new IPA in the private app project, increase its version or build number, and publish to the same public target repository. The source URL stays the same. Then manually start **Refresh app catalog** on `main` in the catalog repository. Only that run adds the new version to the shared source. You do not need another registration entry. There is no schedule, and pushes do not publish the catalog.

A push to the private app repository alone does not publish the IPA to the public download repository. The prepared CI provides private build artifacts and skips automatic release publication in the private repository. Run the local publication command as a separate step. Future automatic publication from private CI would require explicit configuration and appropriate permissions for the second repository; the original repository's `GITHUB_TOKEN` does not receive that access automatically.

The [catalog tools use the MIT license](../LICENSE). You choose the app's license separately. Verify the result in your sideloader and on a physical device.
