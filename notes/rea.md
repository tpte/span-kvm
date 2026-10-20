# Shipped-binary notes

REA `inspect_rust_binary` on `/Applications/Lan Mouse.app/Contents/MacOS/lan-mouse`:

- Mach-O arm64, 4901056 bytes
- SHA-256 `eb4879fe9c718617f3ee91ad88677df484ee56787b46b63e9e86160de38d5ae5`
- No `.dep-v0` dependency section
- A `/rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/` path is present; that only suggests a compiler, it does not prove the build

`open_binary` accepted the same file. Ghidra 12.1.4 started importing it as AARCH64 Apple Silicon and then hit the 330s startup deadline, so there is no procedure listing yet. The loader log did show the linked pieces that matter: `CGEventTapCreate`, AppKit, and a bundled GTK/libadwaita stack. Rust demangling data for AARCH64 was missing (`data/extensions/rust/unix64 does not exist`).

Strings in that image, read directly from the file:

- `CGEventTap disabled by user input, releasing capture state`
- `CGEventTapCreate(kCGSessionEventTap)`
- `releasing capture: release-bind pressed`
- `releasing capture: left remote client device region`
- `did not respond, closing connection`
- `reset_mouse_position called without a connected client`
- DTLS cipher suite names, so the wire path is DTLS, not plain TCP

Input Leap server binary `/Applications/InputLeap.app/Contents/MacOS/input-leaps` still contains the Barrier screen machine: `switchToScreen`, `lockCursorToScreen`, `Input Leap - entering screen`, and a path under `src/lib/platform/OSXScreen.mm`. That is a TCP screen server with the pointer locked to the active screen. It is a different shape from Lan Mouse's edge grab, and it still needs a portal the MSI Hyprland session does not expose.

These notes are behavior and linkage, not a transcript of their source.
