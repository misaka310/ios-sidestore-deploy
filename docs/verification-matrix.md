# Verification Matrix

This file is the evidence index. Keep statuses conservative. A link to CI output is not a substitute for physical-device evidence where a device gate is required.

| ID | Capability | Required evidence | Status | Evidence |
|---|---|---|---|---|
| A1-A5 | Public/free operating assumptions | public repo settings + runner type + Windows workflow record | VERIFIED | [foundation repo](https://github.com/misaka310/ios-sidestore-deploy) and [sample repo](https://github.com/misaka310/ios-sidestore-sample) are Public; run [33659621024](https://github.com/misaka310/ios-sidestore-sample/actions/runs/33659621024) used the standard `macos-14-arm64` runner. |
| B1 | Minimal SwiftUI sample app | separate sample repo + commit | VERIFIED | [sample main merge](https://github.com/misaka310/ios-sidestore-sample/commit/0749814d6d8b78964303702de5934a3a7de3e7fc) |
| B2-B4 | Unsigned hosted macOS build | GitHub Actions run URL + logs showing macOS/Xcode + `.app` artifact | VERIFIED | [run 33659621024](https://github.com/misaka310/ios-sidestore-sample/actions/runs/33659621024), native XCTest job `100346671170`, unsigned build job `100348804281`; logs show `macos-14-arm64`, Xcode 15.4, device-targeted `Release-iphoneos/SideStoreSample.app`, and signing disabled. |
| B5-B8 | IPA packaging/validation | CI run + validator output + build manifest + artifact hash | VERIFIED | [run 33659621024](https://github.com/misaka310/ios-sidestore-sample/actions/runs/33659621024) uploaded artifact `sidestore-sample` ([artifact 9858399234](https://github.com/misaka310/ios-sidestore-sample/actions/runs/33659621024/artifacts/9858399234)); independent validator and manifest schema validation passed. IPA SHA-256: `b4b34faa2afd7adc33155721d7a065dabb7d22313c5d21b60242a72b91f552de`; manifest commit SHA: `23737a1d594fe92d830bcd78af40dfba71967059`; `signed=false`. |
| C1-C2 | Release publication | GitHub Release URL + released IPA SHA-256 | PLANNED | - |
| C3-C5 | AltSource generation/hosting | generator test + source validation + stable HTTPS URL | PLANNED | - |
| C6 | Add source in SideStore | redacted physical-device evidence | PLANNED | - |
| D1-D5 | First physical install | redacted setup evidence + installed version/build + launch proof | PLANNED | - |
| E1-E4 | 7-day refresh lifecycle | timestamped expiry/refresh/launch evidence spanning original expiry boundary | PLANNED | - |
| F1-F5 | One-tap app-version update | version N and N+1 release/source/device evidence | PLANNED | - |
| G1-G4 | Pairing recovery | stale pairing error + local replacement + successful retry, all redacted | PLANNED | - |
| H1-H4 | Security | secret scan/review + workflow permission review + artifact/log review | PLANNED | - |
| I1-I5 | Zero-tap experiment | automation definition + 3 consecutive unattended version upgrades | PLANNED | - |

## Evidence rules

1. Never store Apple Account credentials, pairing files, private keys, provisioning profiles with personal/device data, or private tokens as evidence.
2. Screenshots/logs must redact account email, device identifiers, tokens, and local paths if they reveal private information.
3. For CI, record immutable run/release identifiers and the tested commit SHA.
4. For device tests, record date/time, iOS version, SideStore version/channel, app version/build, LocalDevVPN state, test result, and a short failure note when applicable.
5. Update a status to VERIFIED only when every acceptance criterion represented by that row is satisfied.
6. SUPPORTED means VERIFIED plus incorporated into the normal README/operations workflow.

## Device evidence template

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
