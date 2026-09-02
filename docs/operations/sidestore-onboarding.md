# SideStore onboarding and device evidence

This document is the device-side runbook for the public proof path. It does not store Apple Account information, pairing files, certificates, private keys, provisioning profiles, device identifiers, or personal tokens.

## Official prerequisites

Follow the current [SideStore prerequisites](https://docs.sidestore.io/docs/installation/prerequisites) and [installation guide](https://docs.sidestore.io/docs/installation/install) first. The current guide requires an iPhone/iPad/iPod touch with a passcode and iOS/iPadOS 15 or later, an Apple Account, Wi-Fi, and a computer for initial installation. For Windows, the guide currently calls for 64-bit Windows, iTunes, and iloader; it notes that 32-bit Windows and Windows 10 on ARM are unsupported.

Install LocalDevVPN from the [App Store](https://apps.apple.com/us/app/localdevvpn/id6447489722) and connect it before every SideStore install, update, or refresh. A mobile connection alone is not sufficient.

## First install from Windows

1. Install the Windows prerequisites and iloader using the official guide.
2. Install LocalDevVPN on the iPhone and connect it. Approve the VPN configuration and passcode prompt if shown.
3. Connect the iPhone by USB, trust the computer on the device, open iloader, sign in there with the Apple Account, select the device, and choose `Install SideStore (Stable)`.
4. On the iPhone, trust the developer app under Settings > General > VPN & Device Management. On iOS versions that require it, enable Developer Mode under Settings > Privacy & Security.
5. Open LocalDevVPN and connect, then open SideStore and sign in with the same Apple Account used in iloader.
6. In SideStore > My Apps, tap the `7 DAYS` counter to complete the initial refresh. Approve a certificate refresh prompt only when SideStore displays it.

The exact device prompts can vary by iOS version. If the current official guide differs, follow it and record the difference in the evidence notes rather than silently changing this runbook.

## Add this public source

The verified source URL is:

`https://misaka310.github.io/ios-sidestore-sample/source.json`

SideStore documents the compatible AltSource format and the `sidestore://source?url=[source url]` scheme on its [App Sources guide](https://docs.sidestore.io/docs/advanced/app-sources). When SideStore is already installed, the following link is the supported convenience path:

`sidestore://source?url=https%3A%2F%2Fmisaka310.github.io%2Fios-sidestore-sample%2Fsource.json`

Confirm in SideStore that the source is added and that `SideStore Sample` appears. Keep LocalDevVPN connected while adding/installing. The source contains an unsigned IPA download URL and SHA-256 metadata; signing happens on the iPhone through SideStore, not in GitHub Actions.

## Supported update path

The supported target is a minimum of one user action on SideStore's update action. After a new version is published and visible in the source, connect LocalDevVPN, open SideStore > My Apps, and use the app's update action. Record the number of taps and the installed version/build. Do not describe an update as zero-tap unless the separate experimental gate has three consecutive unattended physical-device successes.

## Pairing recovery

Use the current [official pairing-file guide](https://docs.sidestore.io/docs/advanced/pairing-file) and the dedicated [pairing recovery runbook](pairing-recovery.md): connect the iPhone to the Windows computer, trust it, use iloader's `Delete Stored Pairing`, select the device and trust prompt again, open `Manage Pairing File`, and use `Place` for SideStore. If needed, restart the iPhone and computer and repeat the official procedure.

Pairing files remain local evidence only. Never upload, commit, paste, or attach one to a GitHub issue, release, artifact, source, or chat. The official [common issues](https://docs.sidestore.io/docs/troubleshooting/common-issues) and [error codes](https://docs.sidestore.io/docs/troubleshooting/error-codes) pages are the escalation references.

## Evidence template

Capture only redacted screenshots or notes. Replace account email, device name/UDID, pairing paths, tokens, and personal filesystem paths with `[REDACTED]` before saving evidence anywhere.

```text
Test ID:
Date/time (local):
iOS version:
SideStore version/channel:
App version/build before:
App version/build after:
LocalDevVPN state:
Pairing state:
Action performed:
Expected result:
Actual result:
PASS/FAIL:
Evidence reference (redacted):
Notes:
```

CI success, a release URL, or a reachable source URL is not physical-device evidence. Until the template is completed with actual iPhone observations, C6, D1-D5, E1-E4, F1-F5, and G1-G4 remain unverified in the [verification matrix](../verification-matrix.md).
