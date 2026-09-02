# Acceptance Criteria

## Status vocabulary

- `PLANNED`: documented only.
- `IMPLEMENTED`: code/workflow exists but required proof is incomplete.
- `VERIFIED`: required automated/integration/physical-device evidence passed.
- `SUPPORTED`: verified and adopted as the normal documented workflow.

No criterion may be marked VERIFIED from reasoning alone.

## A. Repository and cost model

- [ ] **A1** Repository is public when using the zero-Actions-minute-cost assumption.
- [ ] **A2** Build jobs use standard GitHub-hosted macOS runners, not larger runners.
- [ ] **A3** Routine source management can be performed from Windows.
- [ ] **A4** No personally owned Mac is required for routine build/release operation.
- [ ] **A5** Default personal-sideloading workflow does not require paid Apple Developer Program membership.

## B. Unsigned macOS build proof

- [ ] **B1** A minimal SwiftUI sample app exists in a separate app repository.
- [ ] **B2** A real GitHub Actions run on a macOS GitHub-hosted runner invokes Xcode tooling successfully.
- [ ] **B3** Build succeeds with code signing disabled and without Apple Account/signing secrets.
- [ ] **B4** Output contains a device-targeted `.app` bundle.
- [ ] **B5** Pipeline creates a structurally valid IPA containing exactly the expected `Payload/<App>.app` root bundle.
- [ ] **B6** IPA validator confirms required `Info.plist` fields and no accidental signing requirement is introduced.
- [ ] **B7** Build manifest records commit, runner/Xcode versions, app version/build, IPA filename, SHA-256, and `signed=false`.
- [ ] **B8** IPA and manifest are uploaded as Actions artifacts.

**Gate:** Do not claim Windows-only/free E2E success before B2-B8 pass in a real hosted run.

## C. Release and AltSource

- [ ] **C1** A version/tag trigger publishes the already-validated IPA to GitHub Releases.
- [ ] **C2** Released IPA hash matches validated build evidence.
- [ ] **C3** AltSource JSON is generated automatically from release metadata.
- [ ] **C4** AltSource passes schema/semantic validation.
- [ ] **C5** AltSource is available at a stable HTTPS URL.
- [ ] **C6** SideStore can add the source on a physical iPhone.

## D. Physical-device installation

- [ ] **D1** SideStore first-time setup is completed using the current official procedure.
- [ ] **D2** LocalDevVPN requirements are documented and observed during install/update/refresh.
- [ ] **D3** Sample IPA downloads from the published source/release path.
- [ ] **D4** SideStore signs and installs the sample app using a free Personal Team context.
- [ ] **D5** Installed app launches and reports the expected version/build.

## E. 7-day lifecycle

- [ ] **E1** Initial expiry/remaining-days state is recorded.
- [ ] **E2** App is refreshed/re-signed before expiry using SideStore.
- [ ] **E3** Evidence confirms the app remains launchable across the original provisioning-expiry boundary because a new provisioning/signing lifecycle was applied.
- [ ] **E4** Documentation accurately states that SideStore manages refresh; it does not claim Apple's 7-day limit disappeared.

## F. Update UX

- [ ] **F1** Version N is installed on a physical device.
- [ ] **F2** Version N+1 is built, released, and added to AltSource automatically.
- [ ] **F3** SideStore detects the new version.
- [ ] **F4** User can complete the supported update with the minimum documented interaction (target: one tap on SideStore's update action).
- [ ] **F5** Version N+1 launches and app data behavior is verified according to the sample app's test design.

One-tap update is the minimum release acceptance target.

## G. Pairing recovery

- [ ] **G1** Recovery procedure is documented from SideStore's current official pairing guidance.
- [ ] **G2** A stale/invalid pairing state is observed or safely simulated on the test device.
- [ ] **G3** Pairing information is replaced locally without exposing the pairing file publicly.
- [ ] **G4** Install/refresh succeeds after recovery.

## H. Security

- [ ] **H1** Repository history contains no Apple credentials, pairing files, signing private keys, sensitive provisioning material, App Store Connect keys, or personal tokens.
- [ ] **H2** Default Actions workflows need no Apple credentials.
- [ ] **H3** Workflow permissions are least-privilege.
- [ ] **H4** Public artifacts/logs contain no device/account secrets.

## I. Zero-tap experimental gate

Zero-tap is optional for the base release and must never block the supported one-tap path.

- [ ] **I1** Candidate automation mechanism is documented with exact prerequisites.
- [ ] **I2** Automation starts without user interaction after its trigger.
- [ ] **I3** Version N -> N+1 completes unattended on a physical iPhone.
- [ ] **I4** Test succeeds for at least 3 consecutive version updates under the same documented conditions.
- [ ] **I5** Failure/recovery behavior is documented.

Only after I1-I5 pass may zero-tap be described as supported. Otherwise it remains experimental/unavailable.

## Final completion gate

The project may be declared complete only when A-H are VERIFIED and evidence is linked from `docs/verification-matrix.md`. Section I is a separate enhancement unless the user explicitly makes zero-tap mandatory for the release.
