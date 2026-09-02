# iOS SideStore Deployment Foundation - Detailed Design

## 1. Purpose

This repository defines a reusable deployment foundation for personal iOS sideloading when the primary development environment is Windows-only. The design separates **artifact production** from **device signing**:

- GitHub-hosted macOS runner: build the app and package an unsigned IPA.
- GitHub Release / AltSource: publish metadata and artifacts.
- SideStore on the iPhone: perform Personal Team signing/refresh on-device using the user's Apple Account.

The repository itself is not an iOS product app. It is infrastructure intended to be reused by downstream app repositories after a sample application proves the full path.

## 2. Design principles

1. **No Apple signing secrets in GitHub.**
2. **Evidence before promotion.** A feature remains experimental until a physical-device test proves it.
3. **Separate supported behavior from research behavior.** One-tap update is the minimum supported target; zero-tap is a later experiment.
4. **Reusable contracts.** Downstream repositories should call reusable workflows instead of duplicating undocumented YAML.
5. **Public-runner cost assumption stays explicit.** The no-minutes-charge assumption applies only to standard GitHub-hosted runners in public repositories under GitHub's current rules.
6. **Recovery is part of the product.** Pairing-file invalidation is an expected failure mode and needs a documented recovery path.
7. **No hidden success criteria.** Every major claim must map to an acceptance criterion and evidence artifact.

## 3. Target architecture

### 3.1 Downstream iOS application repository

Owns Swift/SwiftUI source and project files. After proof, downstream apps call a reusable workflow from this repository with explicit inputs such as project/workspace path, scheme, bundle identifier, version, build number, minimum iOS version, app display name, and release channel.

### 3.2 Reusable macOS build workflow

Runs on a **standard** public-repository GitHub-hosted macOS runner and must:

- select/pin a supported Xcode toolchain;
- run `xcodebuild` with code signing disabled;
- produce a device-targeted `.app` suitable for SideStore re-signing;
- construct `Payload/<App>.app` and zip it as `.ipa`;
- validate archive layout and required `Info.plist` fields;
- calculate artifact hashes;
- upload the IPA as a workflow artifact;
- emit build metadata used by release/source stages.

Because a called workflow runs in the caller repository's workspace, the
workflow must explicitly fetch this foundation repository at a caller-supplied
repository/ref pair before invoking the shared packaging and validation
scripts. The app checkout and the foundation checkout must remain separate so
the workflow cannot silently use stale or caller-local copies of deployment
logic.

No Apple Account credentials, signing certificates, provisioning profiles, or private keys may be required.

### 3.3 Release publisher

On an approved tag/version event, publishes the already-validated IPA to a GitHub Release. The released IPA must be byte-identical to the validated artifact or be revalidated after publication.

### 3.4 AltSource generator

Produces a SideStore-compatible AltStore Source JSON document from release metadata. It must avoid manual version-entry editing and validate duplicate versions, URL fields, app/version/build consistency, and stable ordering.

### 3.5 Stable source hosting

The source JSON needs a stable HTTPS URL. Preferred order:

1. GitHub Pages if practical.
2. Raw GitHub content only if SideStore behavior/caching is explicitly tested.
3. Another free public reproducible host only if necessary.

### 3.6 SideStore device runtime

SideStore performs local signing/installation/refresh. GitHub CI treats SideStore as an external runtime with physical-device acceptance tests instead of assuming success from artifact generation alone.

## 4. Data flow

### Build path

1. Codex or the user modifies the downstream app on Windows.
2. Changes are pushed to GitHub.
3. A GitHub-hosted macOS runner invokes Xcode tooling with signing disabled.
4. CI creates an unsigned `.app`.
5. CI packages `Payload/<App>.app` into `<App>-<version>.ipa`.
6. CI validates IPA structure/metadata and calculates SHA-256.
7. CI uploads the IPA and a machine-readable build manifest.

### Release path

1. A release trigger selects a previously validated commit/version.
2. The pipeline publishes the IPA to GitHub Releases.
3. It records the final download URL and SHA-256.
4. AltSource is generated/updated from release metadata.
5. Source validation runs before publication.
6. The source is published at the stable URL.

### Device path

1. The user installs/configures SideStore using the documented initial setup.
2. The user adds the AltSource.
3. SideStore downloads the remote IPA.
4. SideStore signs it using the user's Personal Team context and installs it.
5. SideStore refreshes/re-signs before expiration when runtime conditions permit.
6. For a new app version, the supported update UX is tested on-device.

## 5. Signing boundary

### GitHub side

Must remain unsigned. CI must not hold or request Apple Account credentials, Personal Team certificates, signing private keys, user/device provisioning profiles, or App Store Connect keys for this path.

### iPhone/SideStore side

The user-side SideStore environment owns signing and refresh. This repository documents how to consume the unsigned IPA but does not reproduce SideStore's Apple authentication/signing process in CI.

## 6. Free provisioning constraints

Current Apple Personal Team constraints are architecture-level requirements:

- App IDs expire after 7 days;
- registered devices expire after 7 days;
- provisioning profiles expire after 7 days;
- up to 3 installed apps per device under the documented free Personal Team limit;
- periodic reprovisioning/refresh is required.

SideStore does not remove these Apple limits. The intended UX is to refresh/re-sign before expiry often enough that a computer reinstall is normally unnecessary.

## 7. Update model

### Supported target: one-tap update

Minimum supported behavior:

1. New release is published.
2. AltSource advertises it.
3. SideStore shows the update.
4. User performs the SideStore-supported update action.
5. New version installs successfully.

This must be proven with two distinct versions on a physical iPhone.

### Experimental target: zero-tap update

Phase 3 only. Candidate mechanisms may include iOS Shortcuts automation using SideStore's documented `sidestore://install?url=...` URL scheme and, only if required, a SideStore fork.

A URL scheme existing is not proof of zero-tap. Zero-tap is accepted only after repeated **unattended** physical-device updates succeed under defined conditions.

## 8. Pairing lifecycle and recovery

Tests/documentation must cover pairing invalidation after iOS update/reset, random pairing invalidation, stale-pairing SideStore errors, pairing replacement through the current SideStore/iLoader flow, and a successful refresh/install after recovery.

No pairing file may be committed, attached to public issues, or uploaded as a public CI artifact.

## 9. Planned implementation layout

```text
127_ios-sidestore-deploy/
├─ README.md
├─ AGENTS.md
├─ docs/
│  ├─ design.md
│  ├─ security.md
│  ├─ acceptance-criteria.md
│  ├─ verification-matrix.md
│  ├─ official-sources.md
│  ├─ operations/
│  │  ├─ sidestore-onboarding.md
│  │  └─ pairing-recovery.md
│  └─ superpowers/plans/
│     └─ 2026-09-03-ios-sidestore-deploy-implementation.md
├─ .github/workflows/
│  ├─ reusable-build-unsigned-ipa.yml
│  ├─ release.yml
│  └─ publish-source.yml
├─ scripts/
│  ├─ package_ipa.sh
│  ├─ validate_ipa.py
│  ├─ generate_alt_source.py
│  └─ validate_alt_source.py
├─ schemas/
│  └─ build-manifest.schema.json
├─ tests/
│  ├─ test_validate_ipa.py
│  ├─ test_generate_alt_source.py
│  └─ fixtures/
└─ source/
   └─ source.json
```

Only documentation exists in Phase 0. Planned code files must not be created merely to make the repository appear complete.

## 10. Build manifest contract

The build stage should emit a manifest with at least:

- `schemaVersion`
- `repository`
- `commitSha`
- `workflowRunId`
- `xcodeVersion`
- `runnerImage`
- `scheme`
- `configuration`
- `bundleIdentifier`
- `appVersion`
- `buildNumber`
- `minimumOSVersion`
- `ipaFileName`
- `ipaSha256`
- `signed=false`
- `buildTimestampUtc`

The manifest is the traceability link between build, release, source generation, and device evidence.

The workflow invocation must also record the foundation repository/ref used for
the packaging and validation scripts in the build evidence, so a later review
can reproduce the exact deployment contract that ran.

## 11. Failure handling

- **CI build failure:** publish nothing.
- **IPA validation failure:** block Release publication.
- **AltSource validation failure:** leave the currently published source unchanged.
- **SideStore install/update failure:** fail the physical-device acceptance gate; do not weaken the gate.
- **Pairing failure:** follow pairing recovery and re-run the same device gate.
- **Zero-tap failure:** keep one-tap as supported behavior; do not make a fork mandatory without evidence and explicit user approval.

## 12. Testing strategy

### Static/local

- Python unit tests for IPA/source validators and source generation.
- Fixture-based valid/invalid IPA tests.
- JSON schema tests for the build manifest.
- Workflow syntax checks where practical.

### GitHub-hosted integration

- public macOS runner actually invokes `xcodebuild`;
- signing is disabled and no Apple secret is needed;
- produced IPA passes validator;
- release/source pipeline operates from a known version.

### Physical device

- first install through SideStore;
- refresh across the free provisioning lifecycle;
- new-version update;
- pairing recovery;
- optional zero-tap experiment.

Physical-device gates are mandatory for claims about SideStore behavior.

## 13. Promotion rules

A capability moves `planned -> implemented -> verified -> supported` only when code exists, relevant automated tests pass, the required integration/device gate passes, evidence is recorded, and documentation is updated accordingly.

## 14. Explicit completion rule

The project must never report "Windows-only free iOS deployment is complete" merely because an IPA file exists. Completion requires the full mandatory acceptance set: unsigned macOS CI build, release/source publication, SideStore device installation, refresh lifecycle proof, pairing recovery, and at least one-tap upgrade between two versions.
