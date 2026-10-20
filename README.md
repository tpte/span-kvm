# span-kvm

Pointer bridge for a Mac in the middle of a Linux machine's screens.

First target: this Mac (`AlandeMacBook-Air`) and the MSI running Omarchy / Hyprland.

## Why this is not Lan Mouse or Input Leap

Both were inspected as shipped binaries, not copied.

Lan Mouse (Mach-O arm64, SHA-256 `eb4879fe9c718617f3ee91ad88677df484ee56787b46b63e9e86160de38d5ae5`) grabs the Mac pointer in a `CGEventTap` as soon as the cursor crosses an edge. It hides the cursor and drops later moves until a release. If the peer stops answering, the binary logs `did not respond, closing connection` and does not show the cursor again. One machine is one rectangle, so a Mac cannot sit between two monitors of the same Linux host.

Input Leap (`input-leaps` / `input-leapc` in InputLeap.app) is a TCP screen server. Its Mac build still contains the Barrier-era `switchToScreen` / `lockCursorToScreen` path. On this MSI the client cannot inject a pointer: Hyprland has no `org.freedesktop.portal.RemoteDesktop`.

span-kvm keeps the local cursor until the peer has acknowledged the enter, and any socket failure returns it to the center of the Mac. The MSI laptop and the BenQ are two edges of one host, not two computers.

## Desk

| Edge of the Mac | Lands on |
| --- | --- |
| Left | MSI laptop (`eDP-2`), near its right side |
| Right | BenQ (`HDMI-A-1`), near its left side |

## Build

Rust toolchain is required. `cargo run -- doctor` prints the desk and the capture rule. The event tap and the Hyprland virtual pointer are not wired up yet.
