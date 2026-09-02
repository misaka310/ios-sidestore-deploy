# SideStore pairing recovery

This is the repository's local-only recovery procedure for Task 11. It follows the current [official SideStore pairing-file guide](https://docs.sidestore.io/docs/advanced/pairing-file). It does not ask the operator to upload or commit the pairing file.

## When to use it

Pairing information may expire after an iPhone update or reset and may also become invalid unexpectedly. Start recovery only from a real stale/invalid pairing failure or a safely available test state; do not erase or reset a device solely to manufacture evidence.

Keep the iPhone and Windows computer available, use a USB cable where possible, and trust the computer on the iPhone if prompted. The official guide says wireless pairing may work, but USB is the more reliable recovery path.

## Local replacement steps

1. Confirm the normal SideStore setup was completed and open iloader on Windows.
2. If iloader offers an update, apply the update according to its prompt.
3. Connect the iPhone by USB, select it in iloader, and accept the device trust prompt.
4. In iloader, select `Delete Stored Pairing` to discard the stale local pairing state.
5. Select the iPhone again and accept the trust prompt on the device.
6. Open `Manage Pairing File` in iloader.
7. Select `Place` beside `SideStore` (and only the apps that are intentionally part of the local setup). Wait for the success message.
8. On the iPhone, connect LocalDevVPN, open SideStore, and retry the previously failing install or refresh.
9. If the error remains, restart the iPhone and Windows computer and repeat the official steps. Use the [official common issues](https://docs.sidestore.io/docs/troubleshooting/common-issues) and [error codes](https://docs.sidestore.io/docs/troubleshooting/error-codes) references before escalating.

The pairing file must stay on the local device/computer path required by iloader. Do not put it in Git, GitHub Releases, Actions artifacts, Pages, screenshots, issue comments, or chat. Redact account email, device name/UDID, and filesystem paths from any evidence.

## G1-G4 evidence record

```text
Test ID: G1/G2/G3/G4
Date/time (local):
iOS version:
SideStore version/channel:
iloader version:
LocalDevVPN state:
Observed stale/invalid error (redacted):
Replacement action:
Install/refresh action after replacement:
Expected result:
Actual result:
PASS/FAIL:
Evidence reference (redacted):
Notes:
```

The existence of this runbook proves G1 documentation only. G2-G4 remain unverified until a real device failure/recovery observation is recorded in redacted form in the [verification matrix](../verification-matrix.md).
