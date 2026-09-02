# iOS SideStore Deploy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and prove a reusable Windows-first pipeline that generates unsigned iOS IPA artifacts on public GitHub-hosted macOS runners, publishes them through GitHub Releases/AltSource, and installs/refreshes them through SideStore without storing Apple signing secrets in GitHub.

**Architecture:** Keep artifact production and device signing separate. GitHub Actions builds/packages/validates an unsigned IPA and publishes release/source metadata; SideStore performs Personal Team signing, installation, update, and refresh on the physical iPhone. Device behavior is promoted only after explicit real-device evidence gates.

**Tech Stack:** Swift/SwiftUI sample app, Xcode/xcodebuild, GitHub Actions, shell packaging on macOS, Python 3 validators/generator, JSON/AltSource, GitHub Releases, SideStore, LocalDevVPN.

**Spec:** `docs/design.md`

## Global Constraints

- Repository must be public when relying on free standard GitHub-hosted runner usage.
- Use standard GitHub-hosted macOS runners only; do not silently switch to larger runners.
- GitHub build path must remain unsigned and require no Apple Account/signing secrets.
- Apple Account credentials, pairing files, signing certificates/private keys, sensitive provisioning profiles, App Store Connect keys, and private tokens must never enter public Git history/artifacts/logs.
- SideStore does not remove Apple's 7-day Personal Team provisioning limit.
- Physical-device behavior is never VERIFIED from CI/static evidence.
- One-tap SideStore update is the supported minimum target.
- Zero-tap update is optional Phase 3 research and remains experimental until 3 consecutive unattended real-device version upgrades pass.
- Do not mark end-to-end complete before all mandatory A-H criteria in `docs/acceptance-criteria.md` are VERIFIED.

---

## Planned file map

Files created in this repository during implementation:

- `.github/workflows/reusable-build-unsigned-ipa.yml` - callable macOS unsigned build workflow.
- `.github/workflows/release.yml` - tag/release publication pipeline.
- `.github/workflows/publish-source.yml` - source generation/validation/publication pipeline if separate from release.
- `scripts/package_ipa.sh` - deterministic `.app` -> `Payload/*.app` -> `.ipa` packager.
- `scripts/validate_ipa.py` - IPA structure and metadata validator.
- `scripts/generate_alt_source.py` - deterministic AltSource updater.
- `scripts/validate_alt_source.py` - source schema/semantic checks.
- `schemas/build-manifest.schema.json` - machine-readable build-evidence contract.
- `tests/test_validate_ipa.py` - IPA validator tests.
- `tests/test_generate_alt_source.py` - source generator/validator tests.
- `tests/fixtures/` - synthetic non-secret fixtures.
- `source/source.json` - generated source state once distribution begins.
- `docs/operations/sidestore-onboarding.md` - first-time device setup procedure.
- `docs/operations/pairing-recovery.md` - pairing invalidation recovery.
- `docs/verification-matrix.md` - evidence index updated as gates pass.

Separate proof app repository planned for implementation: `128_ios-sidestore-sample`. If that number is occupied when execution begins, stop and choose the next unused project number before creating it; do not overwrite an existing repository.

---

### Task 1: Create the minimal SwiftUI proof application

**Files:**
- Create in `128_ios-sidestore-sample`: Xcode project/workspace, minimal SwiftUI app source, README, test target.
- Modify here: `docs/verification-matrix.md`

**Interfaces:**
- Produces: a deterministic scheme named `SideStoreSample`, bundle identifier documented in the sample README, visible version/build label, and a device-targeted Release configuration.
- Consumes: no deployment workflow yet.

- [ ] **Step 1: Create a minimal SwiftUI app with an on-screen version/build label**

The UI must make the installed version observable without Xcode. The app should render `CFBundleShortVersionString` and `CFBundleVersion` from its bundle.

- [ ] **Step 2: Add a test that asserts the app's version/build values are present and non-empty**

Use the native Xcode test target so the sample is not an untested opaque artifact.

- [ ] **Step 3: Run local project validation on a macOS environment available through GitHub Actions later**

Expected first retained proof is the hosted run, not a claim that Windows can run Xcode locally.

- [ ] **Step 4: Commit the sample app independently**

Commit message: `feat: add sidestore deployment proof app`

- [ ] **Step 5: Record B1 evidence in the matrix**

Do not mark B2+ yet.

---

### Task 2: Define build-manifest and IPA validation contracts first

**Files:**
- Create: `schemas/build-manifest.schema.json`
- Create: `scripts/validate_ipa.py`
- Create: `tests/test_validate_ipa.py`
- Create: `tests/fixtures/valid/Payload/Test.app/Info.plist`
- Create synthetic invalid fixture layouts under `tests/fixtures/invalid/`

**Interfaces:**
- `validate_ipa.py` consumes an IPA path and emits a non-zero exit code plus actionable error text on failure.
- Validator output feeds build workflow gating.
- Manifest schema validates fields defined in `docs/design.md`.

- [ ] **Step 1: Write failing tests for invalid IPA roots**

Cases: missing `Payload`, multiple top-level `.app` bundles, missing `Info.plist`, malformed plist, missing bundle identifier, missing version/build.

- [ ] **Step 2: Run the validator tests and confirm they fail because implementation does not exist**

Run: `python -m pytest tests/test_validate_ipa.py -v`

Expected: FAIL for missing validator/import.

- [ ] **Step 3: Implement the minimal read-only IPA validator**

Required checks:

```text
archive opens as ZIP
Payload/ exists
exactly one Payload/*.app root bundle exists
Payload/*.app/Info.plist exists
CFBundleIdentifier exists
CFBundleShortVersionString exists
CFBundleVersion exists
no path traversal entries
```

- [ ] **Step 4: Add passing valid-fixture tests and failure-message assertions**

Run: `python -m pytest tests/test_validate_ipa.py -v`

Expected: PASS.

- [ ] **Step 5: Define and validate the build-manifest JSON schema**

Required keys are the manifest fields listed in `docs/design.md`, including `signed` constrained to `false` for the default workflow.

- [ ] **Step 6: Commit**

Commit message: `test: define unsigned ipa validation contract`

---

### Task 3: Implement deterministic unsigned IPA packaging

**Files:**
- Create: `scripts/package_ipa.sh`
- Extend: `tests/test_validate_ipa.py` if packaging fixtures reveal new validation cases.

**Interfaces:**
- Consumes: path to one unsigned `.app` and output IPA path.
- Produces: ZIP/IPA with `Payload/<App>.app` preserving executable/bundle contents.

- [ ] **Step 1: Define packaging preconditions**

Fail when input `.app` is missing, output exists unexpectedly, or input lacks `Info.plist`.

- [ ] **Step 2: Implement packaging with deterministic directory layout**

Result must be `Payload/<original-name>.app/...` and not nest an extra build directory.

- [ ] **Step 3: Run the validator against the packaged fixture**

Run: `python scripts/validate_ipa.py <generated-fixture.ipa>`

Expected: exit 0.

- [ ] **Step 4: Add negative packaging checks**

Expected failures are explicit and non-zero.

- [ ] **Step 5: Commit**

Commit message: `feat: package unsigned app as validated ipa`

---

### Task 4: Implement the reusable unsigned macOS build workflow

**Files:**
- Create: `.github/workflows/reusable-build-unsigned-ipa.yml`
- Modify: `README.md`

**Interfaces:**
- `workflow_call` inputs: app repository checkout context, scheme, project/workspace selector, configuration, output app name, version/build source.
- Produces: validated IPA artifact + build manifest artifact.

- [ ] **Step 1: Add a workflow-call contract with explicit inputs**

No signing secrets are accepted as inputs or secrets.

- [ ] **Step 2: Add environment/toolchain evidence steps**

Record runner image and `xcodebuild -version` into the build manifest/log.

- [ ] **Step 3: Build with signing disabled**

Planned command shape:

```bash
xcodebuild \
  -scheme "$SCHEME" \
  -configuration Release \
  -sdk iphoneos \
  -derivedDataPath "$RUNNER_TEMP/DerivedData" \
  CODE_SIGNING_ALLOWED=NO \
  CODE_SIGNING_REQUIRED=NO \
  CODE_SIGN_IDENTITY="" \
  build
```

Adjust project/workspace flags according to the sample repo's actual structure; do not add a signing workaround.

- [ ] **Step 4: Locate the built `.app` deterministically**

Fail if zero or multiple candidate app bundles exist instead of picking one arbitrarily.

- [ ] **Step 5: Package and validate the IPA**

Invoke `scripts/package_ipa.sh` then `scripts/validate_ipa.py`.

- [ ] **Step 6: Write the build manifest and validate it against the schema**

Include commit SHA, workflow run ID, Xcode version, runner image, scheme, bundle ID, app version/build, minimum OS version, IPA filename/hash, `signed=false`, UTC timestamp.

- [ ] **Step 7: Upload IPA + manifest as Actions artifacts only after validation succeeds**

- [ ] **Step 8: Commit**

Commit message: `feat: add reusable unsigned ipa build workflow`

---

### Task 5: Execute the mandatory hosted macOS proof gate

**Files:**
- Modify: sample repository workflow caller.
- Modify here: `docs/verification-matrix.md`

**Interfaces:**
- Consumes the reusable workflow from this repository.
- Produces immutable GitHub Actions run evidence.

- [ ] **Step 1: Make both repositories public before relying on the free-public-runner assumption**

Verify repository visibility explicitly.

- [ ] **Step 2: Run the sample build on a standard hosted macOS runner**

No self-hosted or larger runner is acceptable for B2.

- [ ] **Step 3: Verify no Apple signing/account secret is configured or requested**

- [ ] **Step 4: Download the produced IPA/manifest and run independent validation**

- [ ] **Step 5: Record run URL, commit SHAs, artifact names, hashes, runner/Xcode versions in `docs/verification-matrix.md`**

Only now may B2-B8 become VERIFIED if every subcriterion passed.

- [ ] **Step 6: Stop if this gate fails**

Do not proceed to release/source work by assuming the unsigned IPA path is feasible.

---

### Task 6: Implement GitHub Release publication

**Files:**
- Create: `.github/workflows/release.yml`
- Extend tests if release metadata parsing is factored into Python.

**Interfaces:**
- Consumes: a validated build artifact/manifest tied to the release commit/version.
- Produces: GitHub Release with the exact IPA and immutable hash evidence.

- [ ] **Step 1: Define release trigger and version consistency rules**

Reject tags that disagree with the app's declared version.

- [ ] **Step 2: Download/rebuild the exact validated artifact according to one explicit strategy**

Preferred: rebuild deterministically from the tagged commit and validate again, then publish that output. Do not silently publish an unrelated previous-run artifact.

- [ ] **Step 3: Publish IPA using least-privilege repository permissions**

- [ ] **Step 4: Verify released asset hash**

- [ ] **Step 5: Record C1-C2 evidence**

- [ ] **Step 6: Commit**

Commit message: `feat: publish validated ipa releases`

---

### Task 7: Implement AltSource generation and validation

**Files:**
- Create: `scripts/generate_alt_source.py`
- Create: `scripts/validate_alt_source.py`
- Create: `tests/test_generate_alt_source.py`
- Create: `source/source.json`
- Create: `.github/workflows/publish-source.yml` if not folded into release workflow.

**Interfaces:**
- Consumes: app identity metadata + GitHub Release download URL/version/build/date/size.
- Produces: deterministic SideStore-compatible AltSource JSON.

- [ ] **Step 1: Write failing generator tests**

Cover first version, adding a newer version, replacing an exact duplicate idempotently, rejecting conflicting duplicate version/build, and stable output ordering.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_generate_alt_source.py -v`

- [ ] **Step 3: Implement generator and validator**

Preserve only supported AltSource fields. Do not add notarization/marketplace-only fields unless official SideStore/AltSource docs require them for this path.

- [ ] **Step 4: Run tests**

Expected: PASS.

- [ ] **Step 5: Publish source at a stable HTTPS URL**

Prefer GitHub Pages if it satisfies the final URL/caching behavior.

- [ ] **Step 6: Record C3-C5 evidence**

- [ ] **Step 7: Commit**

Commit message: `feat: generate and publish sidestore source`

---

### Task 8: Document and execute first SideStore device installation

**Files:**
- Create: `docs/operations/sidestore-onboarding.md`
- Modify: `docs/verification-matrix.md`

**Interfaces:**
- Consumes: official SideStore prerequisites/install docs, stable source URL, released IPA.
- Produces: redacted real-device evidence for C6/D1-D5.

- [ ] **Step 1: Re-check official SideStore setup docs on the execution date**

Do not copy stale third-party instructions.

- [ ] **Step 2: Document Windows initial setup, device trust, Developer Mode when required, Apple Account login, Wi-Fi, and LocalDevVPN requirements**

- [ ] **Step 3: Add the source on the physical iPhone**

- [ ] **Step 4: Install the sample app through SideStore**

- [ ] **Step 5: Launch it and capture the visible version/build**

- [ ] **Step 6: Record redacted C6/D1-D5 evidence**

Do not store the Apple Account email, pairing file, UDID, or signing material.

---

### Task 9: Prove the 7-day refresh lifecycle

**Files:**
- Modify: `docs/verification-matrix.md`
- Modify onboarding/operations docs only if observed behavior differs from assumptions.

**Interfaces:**
- Consumes: installed sample app and SideStore runtime.
- Produces: timestamped E1-E4 evidence spanning the original provisioning-expiry boundary.

- [ ] **Step 1: Record the initial remaining-days/expiry state**

- [ ] **Step 2: Refresh/re-sign before expiry using SideStore with required network/VPN state**

- [ ] **Step 3: Record the new validity state**

- [ ] **Step 4: After the original profile would have expired, confirm the app still launches because the refresh produced a renewed signing/provisioning state**

- [ ] **Step 5: Mark E1-E4 VERIFIED only if the evidence spans the original boundary**

A same-day manual refresh is not sufficient proof for E3.

---

### Task 10: Prove one-tap app-version update

**Files:**
- Modify sample app version/build.
- Modify: `docs/verification-matrix.md`

**Interfaces:**
- Consumes: working release/source/device path.
- Produces: F1-F5 evidence across version N -> N+1.

- [ ] **Step 1: Keep version N installed and record it**

- [ ] **Step 2: Change the sample app visible behavior plus version/build to N+1**

A visible behavior change prevents falsely accepting a metadata-only mismatch.

- [ ] **Step 3: Build/release/update AltSource through the automated pipeline**

- [ ] **Step 4: Confirm SideStore detects N+1**

- [ ] **Step 5: Perform the documented minimum interaction (target: one update tap)**

- [ ] **Step 6: Launch N+1 and verify both the version/build and visible behavior change**

- [ ] **Step 7: Record F1-F5 evidence**

---

### Task 11: Document and prove pairing recovery

**Files:**
- Create: `docs/operations/pairing-recovery.md`
- Modify: `docs/verification-matrix.md`

**Interfaces:**
- Consumes: current official SideStore pairing-file guidance and a stale/invalid pairing state.
- Produces: G1-G4 evidence.

- [ ] **Step 1: Re-check SideStore's official pairing-file page**

- [ ] **Step 2: Document local replacement steps using current iLoader terminology**

- [ ] **Step 3: Observe or safely simulate a stale pairing failure**

Do not deliberately erase/reset the device solely to create evidence.

- [ ] **Step 4: Replace pairing information locally**

- [ ] **Step 5: Confirm install/refresh works again**

- [ ] **Step 6: Record only redacted evidence; never commit the pairing file**

---

### Task 12: Perform the security and completion review

**Files:**
- Modify: `docs/verification-matrix.md`
- Modify: `README.md` only after evidence supports stronger status wording.

**Interfaces:**
- Consumes all previous evidence.
- Produces supported/unsupported project-status decision.

- [ ] **Step 1: Review repository history and Actions configuration for prohibited secrets**

- [ ] **Step 2: Verify default workflows require no Apple signing credentials**

- [ ] **Step 3: Verify Actions permissions are least-privilege and public artifacts/logs contain no private device/account material**

- [ ] **Step 4: Check every A-H acceptance checkbox against the evidence matrix**

- [ ] **Step 5: Update README status to SUPPORTED only if all A-H are VERIFIED**

If any mandatory item is missing, state the exact remaining gap instead of declaring completion.

- [ ] **Step 6: Commit**

Commit message: `docs: record deployment foundation verification`

---

### Task 13: Optional Phase 3 zero-tap update research

**Files:**
- Create only after A-H are supported: `docs/research/zero-tap-update.md`
- Modify: `docs/verification-matrix.md`

**Interfaces:**
- Consumes: stable released IPA URL and SideStore URL scheme.
- Produces: I1-I5 evidence or a documented unsupported result.

- [ ] **Step 1: Re-check SideStore's current URL-scheme documentation**

Baseline documented operation: `sidestore://install?url=[download url]`.

- [ ] **Step 2: Test whether an iOS Shortcut automation can invoke the install flow unattended under the user's actual iOS version/settings**

- [ ] **Step 3: Identify every user-confirmation/background restriction encountered**

- [ ] **Step 4: Only if the supported SideStore path cannot meet the requirement, evaluate a SideStore fork as a separate architecture decision**

Do not silently introduce a fork into the base product.

- [ ] **Step 5: Run 3 consecutive unattended N -> N+1 style version upgrades**

- [ ] **Step 6: Promote zero-tap to SUPPORTED only if all I1-I5 pass**

Otherwise document the failure mode and retain one-tap as the supported UX.

---

## Implementation execution order

Execute Tasks 1-5 first and stop immediately if the hosted unsigned build proof fails. Only after B2-B8 are VERIFIED proceed to release/source work (Tasks 6-7). Then execute physical-device Tasks 8-11. Task 12 is the mandatory release gate. Task 13 is optional research and must not contaminate the supported base design.

## Plan self-review result

- Spec coverage: architecture, security boundary, cost assumption, unsigned IPA proof, Release, AltSource, SideStore installation, 7-day refresh, one-tap update, pairing recovery, and zero-tap research are all mapped to tasks.
- Placeholder check: no `TBD`/`TODO` implementation gaps are accepted as instructions. Runtime values such as URLs/SHAs are evidence produced during execution, not unspecified design decisions.
- Success discipline: hosted macOS proof and physical-device gates remain hard gates; implementation cannot promote itself by weakening them.
