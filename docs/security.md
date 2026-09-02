# Security Model

## Security objective

Keep public CI and public Git history free of Apple-account, device-pairing, and signing secrets. The build pipeline produces unsigned artifacts; SideStore/iPhone handles Personal Team signing.

## Forbidden repository/CI data

Never commit, upload as an Actions artifact, attach to a public issue, or print in logs:

- Apple Account username/password or session material
- anisette/account authentication material
- `.mobiledevicepairing` or equivalent pairing records
- signing certificates
- certificate private keys
- provisioning profiles tied to a user/device unless fully proven non-sensitive and explicitly required (default: prohibited)
- App Store Connect API keys
- personal access tokens
- device identifiers when unnecessary for public evidence

## GitHub Actions rules

1. Default unsigned build must require no Apple secrets.
2. Workflows must use least-privilege `permissions`.
3. Release/source publication may use `GITHUB_TOKEN` with only the repository permissions required by the job.
4. Third-party actions should be minimized and pinned to immutable commit SHAs when practical.
5. Logs must not dump environment variables or authentication material.
6. Public build artifacts may contain only distributable IPA/build-manifest/source data intended for publication.

## Device-side rules

- Pairing information remains on trusted local devices only.
- Apple Account authentication is entered only into the supported local SideStore/iLoader flow.
- Recovery instructions must never ask the user to paste secrets into GitHub, ChatGPT, CI logs, or public issue trackers.

## Threat model

### Public-repository secret leakage

Mitigation: architecture does not need Apple signing credentials in CI; add secret-pattern checks later and document prohibited files.

### Supply-chain compromise in GitHub Actions

Mitigation: minimize third-party actions, pin dependencies, use explicit permissions, and validate produced artifacts.

### Release/source mismatch

Mitigation: hash IPA artifacts and carry the SHA-256 through the build manifest/release evidence. Source generation must consume verified release metadata.

### Malicious or accidental IPA replacement

Mitigation: release validation checks filename/version/hash; physical-device evidence records the installed version/build.

### Pairing-file exposure

Mitigation: pairing files are never repository inputs. Recovery occurs locally and the verification matrix stores only redacted evidence.

## Incident response

If sensitive material is ever committed or published:

1. Treat it as compromised immediately.
2. Revoke/rotate the relevant credential or pairing/signing material where possible.
3. Remove it from the current repository state.
4. Rewrite Git history only when required; deleting the latest file alone is not sufficient if the secret remains in history.
5. Invalidate public artifacts/caches containing the secret.
6. Document the incident without copying the secret into the incident record.

## Security acceptance gate

Implementation cannot be accepted until a repository-wide review confirms that the unsigned build works without Apple secrets and that no prohibited secret-bearing files are tracked.
