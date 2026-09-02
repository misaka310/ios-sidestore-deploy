# Official Sources Checked for the Design

Checked on 2026-09-03 (JST). Re-check these sources before implementation if SideStore, Apple Personal Team rules, GitHub Actions billing, or runner images change.

## Apple Developer

### Developer account overview / Personal Team

https://developer.apple.com/help/account/basics/about-your-developer-account/

Design facts taken from this page:

- Personal Team is available when an Apple Account is not associated with Apple Developer Program membership.
- Up to 10 App IDs can be registered and they expire after 7 days.
- Up to 3 devices can be registered and they expire after 7 days.
- Up to 3 apps can be installed per device.
- Provisioning profiles used for device installation expire 7 days after issuance.
- Apps must be reprovisioned/reinstalled after profile expiry if they were not refreshed/re-signed through the chosen workflow.

Japanese membership comparison page:

https://developer.apple.com/jp/support/compare-memberships/

## SideStore

### Installation prerequisites

https://docs.sidestore.io/docs/installation/prerequisites

Design facts:

- Initial setup supports a Windows computer.
- Apple Account and Wi-Fi are required.
- LocalDevVPN is part of the current setup.
- LocalDevVPN must be enabled when installing, updating, or refreshing apps.

### Installation

https://docs.sidestore.io/docs/installation/install

Design facts:

- Initial install uses a computer/iLoader flow and a device connection/trust step.
- SideStore exposes a 7-day remaining counter and a manual refresh action.
- Developer Mode setup is part of the current documented installation procedure for applicable iOS versions.

### Pairing file

https://docs.sidestore.io/docs/advanced/pairing-file

Design facts:

- Pairing data can expire after iOS update/reset and may also become invalid unexpectedly.
- Recovery uses iLoader to replace the pairing information.

### App sources

https://docs.sidestore.io/docs/advanced/app-sources

Design facts:

- SideStore is compatible with AltStore Sources / AltSources.
- Sources provide app/version discovery and updates.

### AltSource format and updates

https://faq.altstore.io/developers/make-a-source
https://faq.altstore.io/developers/updating-apps

Design facts:

- A source contains an ordered `apps` array; each app has an ordered `versions` array.
- App versions use `version`, `buildVersion`, `date`, `downloadURL`, and `size`; `minOSVersion` is supported for compatibility filtering.
- `sha256` is supported for verifying a downloaded IPA, so the generated source carries the release asset hash.
- Updates are detected from the first compatible version entry, so the generator keeps the newest version/build first.
- The source implementation intentionally excludes marketplace-only `marketplaceID` and `Build` fields because the SideStore documentation warns that those fields can cause a source to be treated as notarized.

### URL scheme

https://docs.sidestore.io/docs/advanced/url-schema

Design facts:

- Remote IPA installation can be opened with `sidestore://install?url=[download url]`.
- An AltSource can be added with `sidestore://source?url=[source url]`.
- Current documented URL-scheme functionality is limited, so existence of the scheme is not proof of unattended updating.

### Common issues / error codes

https://docs.sidestore.io/docs/troubleshooting/common-issues
https://docs.sidestore.io/docs/troubleshooting/error-codes

Used to support the operational design around LocalDevVPN/Wi-Fi requirements and pairing-file replacement when SideStore cannot refresh/install correctly.

## GitHub Actions

### GitHub Actions billing

https://docs.github.com/en/billing/concepts/product-billing/github-actions

Design fact:

- Standard GitHub-hosted runner usage is free for public repositories. Private repositories use plan allowances and may incur charges after the included quota.

### GitHub-hosted runners reference

https://docs.github.com/en/actions/reference/runners/github-hosted-runners

Design facts:

- Standard macOS GitHub-hosted runner labels are available for public repositories.
- Public repositories can use standard GitHub-hosted runners without Actions-minute charges under the documented model.
- Larger runners are a separate paid category and are excluded from this project's zero-cost assumption.

## Interpretation boundary

Official documentation confirms the building blocks and limits above. It does **not** by itself prove that this repository's exact unsigned-Xcode-build -> IPA -> SideStore path works end to end. That is why the implementation plan requires a hosted macOS proof and physical-device gates before any completion claim.
