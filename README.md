# 127_ios-sidestore-deploy

Reusable deployment foundation for building unsigned iOS IPA artifacts on GitHub-hosted macOS runners and distributing them through a SideStore-compatible AltSource, while keeping Apple Account credentials and device-specific signing material off GitHub.

> Repository number note: the original draft name was `126_ios-sidestore-deploy`, but `126_fictional-cm-studio` already exists locally. This repository therefore uses `127_` to keep project numbering unique.

## Status

**Implementation in progress. The separate proof app for B1 exists, but the hosted macOS build and all release/device gates remain unverified.**

The repository is not considered end-to-end complete until every required real-device gate in `docs/acceptance-criteria.md` has passed. Generating an unsigned IPA on a GitHub-hosted macOS runner is an explicit early proof gate. Zero-tap app-version updates remain experimental until repeated unattended real-device success is demonstrated.

## Goal

Provide a reusable deployment base that allows an iOS app to be developed and maintained from a Windows-only primary environment without owning a Mac and without requiring paid Apple Developer Program membership for the intended personal sideloading workflow.

Target flow:

`Codex modifies app -> push to GitHub -> macOS GitHub Actions builds unsigned app/IPA -> GitHub Release publishes IPA -> AltSource JSON updates -> SideStore detects the version -> iPhone signs/installs locally`

Signing is intentionally **not** performed in GitHub Actions. SideStore/iPhone-side signing remains separate from artifact production.

## Non-goals

- App Store distribution.
- Paid Apple Developer Program certificate management in GitHub Actions.
- Storing Apple Account credentials, pairing files, signing certificates, private keys, provisioning profiles, or personal tokens in this repository.
- Claiming that SideStore removes Apple's 7-day Personal Team provisioning limit.
- Claiming that a new app version updates with zero taps unless this has been repeatedly proven on a physical device.

## Current verified platform facts

The design must be revalidated before implementation if any source changes materially.

- Apple Personal Team/free provisioning has periodic reprovisioning limits. Apple currently documents up to 10 App IDs and up to 3 devices that expire after 7 days, up to 3 installed apps per device, and provisioning profiles that expire 7 days after issuance.
- SideStore's documented prerequisites include an Apple Account, an initial computer-based setup, Wi-Fi, and LocalDevVPN. LocalDevVPN is required when installing, updating, or refreshing apps.
- SideStore pairing information can become invalid after device updates/resets and can also expire unexpectedly; recovery requires replacing the pairing file.
- SideStore supports AltStore-compatible app sources (AltSources).
- SideStore documents `sidestore://install?url=[download url]` for opening a remote IPA install and `sidestore://source?url=[source url]` for adding a source.
- GitHub documents standard GitHub-hosted runners as free for public repositories; standard public macOS runners are included. Larger runners are not part of that free-public-repository assumption.

See `docs/official-sources.md` for the authoritative references checked during design.

## Repository responsibilities

This repository is the reusable deployment foundation, not the product app itself. Future iOS app repositories should consume reusable workflows/scripts/contracts from here rather than copy undocumented build logic.

Planned responsibilities:

1. Define a deterministic unsigned iOS build contract.
2. Package a valid `.ipa` artifact from the unsigned `.app` output.
3. Validate the IPA structure before publishing it.
4. Publish versioned IPA assets to GitHub Releases.
5. Generate/update a SideStore-compatible AltSource JSON document.
6. Publish the source document at a stable URL.
7. Document first-time SideStore onboarding and pairing recovery.
8. Define evidence gates for 7-day refresh, one-tap update, and experimental zero-tap update behavior.
9. Expose reusable GitHub Actions workflows for downstream app repositories after the prototype proves the path.

## Required reading order for Codex

1. `README.md`
2. `docs/design.md`
3. `docs/security.md`
4. `docs/acceptance-criteria.md`
5. `docs/verification-matrix.md`
6. `docs/superpowers/plans/2026-09-03-ios-sidestore-deploy-implementation.md`
7. `docs/official-sources.md`

## Phase gates

### Phase 0 - documentation

Complete when the design, security boundary, implementation plan, evidence model, and acceptance criteria are internally consistent. This is the current phase.

### Phase 1 - unsigned build and distribution proof

Must prove, in order:

1. Minimal SwiftUI app exists in a separate sample app repository.
2. Public-repository macOS GitHub Actions builds an unsigned `.app` without Apple signing secrets.
3. A correctly structured `.ipa` is produced and validated.
4. The IPA is retained as an Actions artifact.
5. A tagged GitHub Release publishes the exact verified IPA.
6. AltSource JSON is generated from release metadata and passes validation.
7. SideStore can add the source and install the app on a physical iPhone.

**Do not claim Windows-only/free end-to-end completion before step 2 succeeds on GitHub's macOS runner and the physical-device install gate later succeeds.**

### Phase 2 - lifecycle proof

1. Observe and record refresh behavior across the Personal Team validity window.
2. Verify the app remains usable because it was refreshed/re-signed before expiry.
3. Publish a new version and verify the supported minimum-update UX on a physical iPhone.
4. Verify pairing-file recovery from a deliberately invalid/expired state.

### Phase 3 - zero-tap research

Investigate Shortcuts/automation using SideStore's documented URL scheme and, only if necessary, a SideStore fork. Zero-tap is **experimental** until unattended physical-device updates succeed repeatedly under explicit test criteria.

## Security boundary

Never commit:

- Apple Account username/password or session material
- pairing files / mobiledevice pairing records
- signing certificates or private keys
- provisioning profiles containing personal/device data
- App Store Connect API keys
- personal access tokens or other private tokens

GitHub Actions should not require Apple Account credentials for the default architecture.

## Definition of done

The platform is accepted only when all mandatory criteria in `docs/acceptance-criteria.md` are evidenced. The intended final state includes:

- no personally owned Mac required for routine build/release work;
- no paid Apple Developer Program membership required for this personal sideloading path;
- public GitHub repository using standard GitHub-hosted macOS runners with no Actions-minute charge under GitHub's documented public-repository model;
- Windows-based source management;
- deterministic unsigned IPA generation on GitHub-hosted macOS;
- SideStore installation on a physical iPhone;
- successful refresh/re-sign operation observed across the 7-day provisioning lifecycle;
- documented and tested pairing recovery;
- at least a one-tap supported update flow for a new version;
- zero-tap update support only if repeated unattended real-device tests pass.

Until those evidence gates pass, status must remain partial/experimental rather than "complete".
