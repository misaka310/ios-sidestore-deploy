# Repository instructions

## 仕様の正本

- 仕様の正本: `docs/design.md`
- 実装前に意図する仕様を正本へ反映し、仕様変更時は同じ変更で正本、実装、検証を更新する。

## Repository purpose

This repository is the reusable deployment foundation for building unsigned iOS IPA artifacts on GitHub-hosted macOS runners and distributing them through a SideStore-compatible source. It is not an iOS product app.

## Specification gate

- Code, dependency, workflow, and test implementation must not begin before the intended behavior is reflected in `docs/design.md`.
- Mutable project status belongs in `README.md` and `docs/verification-matrix.md`, not in this instruction file.

## Non-negotiable constraints

- Never place Apple Account credentials, pairing files, signing certificates/private keys, provisioning profiles, App Store Connect keys, or personal tokens in Git or public CI artifacts.
- Default GitHub build architecture must remain unsigned; signing occurs on the iPhone/SideStore side.
- Do not claim SideStore removes Apple's 7-day Personal Team provisioning limit.
- Do not claim zero-tap app-version updates are supported until repeated unattended physical-device tests pass.
- Do not claim end-to-end completion from an IPA build alone; use `docs/acceptance-criteria.md`.
- The no-Actions-minute-charge assumption applies only to standard GitHub-hosted runners in a public repository under current GitHub rules.

## Required reading before implementation

1. `README.md`
2. `docs/design.md`
3. `docs/security.md`
4. `docs/acceptance-criteria.md`
5. `docs/verification-matrix.md`
6. `docs/superpowers/plans/2026-09-03-ios-sidestore-deploy-implementation.md`
7. `docs/official-sources.md`

## Success discipline

Every capability must be classified as planned, implemented, verified, or supported. Physical-device behavior cannot be promoted to verified/supported from static reasoning or CI-only evidence.
