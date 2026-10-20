# span-kvm input and handoff program plan

Alan 需要 Mac 與 MSI 三屏 KVM 的切邊、中鍵、滾輪、鍵盤與中文輸入都可靠。PR 順序為 PR1、PR2、PR3、PR4。

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `playbooks/autopilot-stack.md`. Alan lands the stack bottom-up after merge-ready reports.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator's explicit go.
- [ ] Read these from trunk at program start.
  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/autopilot-stack.md`
  - [ ] `git show origin/main:pstack/skills/swarm/SKILL.md`
  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/opening-a-pr.md`
- [ ] On the operator's go, arm `/loop 1h` with the standard audit tick. The tick posts a short status message to the operator in chat only when progress changed.

### Spawn owners

- [ ] PR1 and PR2 stack from `main`. PR3 after PR2. PR4 after PR3.
- [ ] Hold file boundaries to `host/**`, `layout.json`, and `notes/**`.

### PR mechanics, for every PR

- [ ] Run `cd host && python3 -m unittest discover -v` before push.
- [ ] Open PR ready per Opening a PR playbook.

### Verdict and merge, for every PR

- [ ] Full swarm at code-ready head per swarm skill.
- [ ] Merge only on clean verdict and rebased trunk.

### Boot recipe, for every live lane

- [ ] Checkout PR head SHA on a lane VM.
- [ ] Start Mac and MSI daemons. Wait for listen on port 42421.
- [ ] Drive input only through physical edge cross and logged scenarios.
- [ ] Save screenshots under `/tmp/swarm-<pr-id>/worker-<n>/<slug>.png`.

## Add protocol tests and RemoteSession (PR1)

**Depends on.** None.

**Files.**

- [x] Create `host/session.py`.
- [x] Create `host/test_session.py`, `host/test_keys.py`, `host/test_enter.py`.
- [x] Refactor `host/msi.py` to use `RemoteSession`.

**Build.**

- [x] Encode MSI messages in `RemoteSession.feed` with injectable sink.

**You see.**

- [x] Unit discover reports at least 24 passing cases.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `cd host && python3 -m unittest discover -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head.

- [ ] Lane 1. Regression against trunk. Trunk lacks `RemoteSession`. Save `regression-enter.png`. Pass when Mac cursor hides and only MSI pointer moves after left enter.
- [ ] Lane 2. Middle click on MSI after left enter. Save `middle-click.png`. Pass when middle click reaches a focused MSI target.
- [ ] Lane 3. Type hello on MSI remote. Save `type-hello.png`. Pass when characters appear in a text field.
- [ ] Lane 4. Chinese IME one phrase on MSI. Save `ime-phrase.png`. Pass when composed text appears or PR3 is flagged blocked.
- [ ] Lane 5. Scroll wheel in MSI browser. Save `scroll.png`. Pass when page scrolls after PR2 or lane notes blocked.
- [ ] Lane 6. Slide back from MSI main seam to Mac. Save `back-main.png`. Pass when Mac cursor height matches seam without center snap.
- [ ] Lane 7. Right Mac edge to MSI ext and back. Save `back-ext.png`. Pass when return lands on correct Mac x.
- [ ] Lane 8. Chord release returns to Mac. Save `chord-release.png`. Pass when Mac cursor is visible again.
- [ ] Lane 9. Kill MSI daemon during remote. Save `disconnect-guard.png`. Pass when Mac cursor returns within ACK timeout.
- [ ] Lane 10. Desk UI layout drag then re-enter edge. Save `desk-layout.png`. Pass when handoff still works on new seam.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time from Mac edge cross to first MSI ack in Mac log.
- [ ] Probe. Ten edge crosses with log timestamps on trunk then head interleaved.
- [ ] Baseline. Record trunk p95 first before PR1 lands.
- [ ] Rule. Head p95 must not exceed trunk p95 plus 50 ms with MSI-only motion within 1.0 s ACK.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane 1 and lane 6 screenshots for the operator review packet.
- [ ] Record a 30 to 60 second handoff video for the operator.
- [ ] Post screenshots and video in chat and wait for the operator click to merge.

**Merge.**

- [ ] Root clean verdict at exact head SHA.

## Forward scroll wheel and fractional move (PR2)

**Depends on.** PR1 merged into stack base.

**Files.**

- [x] Edit `host/gate.py`, `host/mac.py`, and `host/msi.py`.

**Build.**

- [x] Route scroll in `remote`, emit `REL_WHEEL` and `REL_HWHEEL`, round fractional move deltas.

**You see.**

- [x] Scroll and round-delta unit tests pass.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `cd host && python3 -m unittest discover -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head.

- [ ] Lane 1. Regression scroll down in MSI browser. Save `scroll-down.png`. Pass when content moves down.
- [ ] Lane 2. Regression scroll up in MSI browser. Save `scroll-up.png`. Pass when content moves up.
- [ ] Lane 3. Horizontal scroll if app supports it. Save `scroll-h.png`. Pass when horizontal motion occurs or lane records unsupported.
- [ ] Lane 4. Fast diagonal pointer on MSI. Save `diagonal-move.png`. Pass when path looks smooth without staircase drift.
- [ ] Lane 5. Middle click after scroll. Save `middle-after-scroll.png`. Pass when both work in one session.
- [ ] Lane 6. Left enter then scroll then back seam. Save `scroll-back.png`. Pass when Mac return still works.
- [ ] Lane 7. Right enter scroll on ext monitor. Save `ext-scroll.png`. Pass when ext monitor scrolls.
- [ ] Lane 8. Type after scroll on MSI. Save `type-after-scroll.png`. Pass when keys still work.
- [ ] Lane 9. Chord release after scroll session. Save `chord-after-scroll.png`. Pass when Mac regains cursor.
- [ ] Lane 10. Desk UI unchanged scroll smoke. Save `desk-scroll-smoke.png`. Pass when layout load does not break scroll.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Move messages per second during fast circle on MSI.
- [ ] Probe. Same circle gesture on PR1 head then PR2 head interleaved.
- [ ] Baseline. Record PR1 head message rate first.
- [ ] Rule. PR2 head rate within 10 percent of PR1 head at the same physical speed.

**Review gate.** The operator reviews before merge.

- [ ] Save scroll lane screenshot for operator review.
- [ ] Record scroll video for the operator.
- [ ] Post screenshot and video in chat and wait for the operator merge click.

**Merge.**

- [ ] Squash merge PR2 after operator review and clean swarm.

## Fix keyboard modifiers and IME (PR3)

**Depends on.** PR2 merged.

**Files.**

- [ ] Edit `host/mac.py` and `host/keys.py`.
- [ ] Create `host/test_mac_modifiers.py`.

**Build.**

- [ ] Sync held Mac modifiers to MSI on ack using `MODIFIER_BITS` linux codes.

**You see.**

- [ ] Chinese IME lane 4 passes on MSI hardware.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Modifier sync tests pass in `test_mac_modifiers.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head.

- [ ] Lane 1. Regression hello typing on MSI. Save `type-hello-pr3.png`. Pass when hello appears.
- [ ] Lane 2. Chinese IME phrase. Save `ime-phrase-pr3.png`. Pass when phrase commits to field.
- [ ] Lane 3. Shift plus letter on MSI. Save `shift-letter.png`. Pass when uppercase appears.
- [ ] Lane 4. Ctrl plus letter shortcut if app bound. Save `ctrl-shortcut.png`. Pass when shortcut fires or lane notes no binding.
- [ ] Lane 5. Meta key browser shortcut smoke. Save `meta-smoke.png`. Pass when expected browser action or lane notes skip.
- [ ] Lane 6. Modifier held before edge cross stays effective on MSI. Save `mod-before-enter.png`. Pass when remote typing respects held mod.
- [ ] Lane 7. Release chord clears MSI keys. Save `upall-keys.png`. Pass when no stuck key repeats on MSI.
- [ ] Lane 8. Return to Mac then type locally. Save `mac-after-remote-type.png`. Pass when Mac IME still works.
- [ ] Lane 9. Number row and symbols. Save `symbols.png`. Pass when digits and punctuation map correctly.
- [ ] Lane 10. Function key smoke if mapped. Save `fn-smoke.png`. Pass when mapped keys work or lane lists gaps.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Key event latency from Mac tap to uinput on MSI via log correlation.
- [ ] Probe. Ten key down events measured on PR2 head then PR3 head interleaved.
- [ ] Baseline. Record PR2 head p95 first.
- [ ] Rule. PR3 head p95 not worse than PR2 head p95 plus 15 ms.

**Review gate.** The operator reviews before merge.

- [ ] Save IME lane screenshot for operator review.
- [ ] Record typing video for the operator.
- [ ] Post screenshot and video in chat and wait for the operator merge click.

**Merge.**

- [ ] Squash merge PR3 after operator review and clean swarm.

## Smooth edge transition and jitter (PR4)

**Depends on.** PR3 merged.

**Files.**

- [ ] Edit `host/mac.py`.
- [ ] Optional edit `host/session.py` for sub-pixel accumulator.

**Build.**

- [ ] Tune `quiet_until` and waiting phase edge logic from measured handoff traces.

**You see.**

- [ ] Operator reports no floaty cursor during enter and back on daily use.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Layout and gate tests still pass after timing tweaks.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head.

- [ ] Lane 1. Regression left enter ten times. Save `enter-repeat.png`. Pass when no stuck waiting phase.
- [ ] Lane 2. Regression right enter ten times. Save `enter-right-repeat.png`. Pass when same on ext path.
- [ ] Lane 3. Fast back seam ten times. Save `back-repeat.png`. Pass when Mac y stays consistent.
- [ ] Lane 4. Slow edge hover without false enter. Save `edge-hover.png`. Pass when Mac does not flicker hide.
- [ ] Lane 5. Move burst after enter. Save `burst-move.png`. Pass when MSI tracking keeps up.
- [ ] Lane 6. Click immediately after enter. Save `fast-click.png`. Pass when click lands on MSI target.
- [ ] Lane 7. Dual monitor round trip left then right. Save `round-trip.png`. Pass when both seams work in one minute.
- [ ] Lane 8. Disconnect during waiting phase. Save `waiting-disconnect.png`. Pass when Mac recenters safely.
- [ ] Lane 9. Desk UI tweak mid session. Save `layout-mid-session.png`. Pass when next enter uses new layout.
- [ ] Lane 10. Long session ten minute mixed use. Save `long-session.png`. Pass when no cursor lock at end.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. p95 Mac to MSI enter and p95 MSI back to visible Mac cursor.
- [ ] Probe. Twenty handoffs interleaved PR3 head then PR4 head.
- [ ] Baseline. Record PR3 head p95 pair first.
- [ ] Rule. Each PR4 p95 improves 20 percent vs PR3 or stays under 120 ms absolute.

**Review gate.** The operator reviews before merge.

- [ ] Save handoff screenshot for operator review.
- [ ] Record bidirectional handoff video for the operator.
- [ ] Post screenshot and video in chat and wait for the operator merge click.

**Merge.**

- [ ] Squash merge PR4 after operator review and clean swarm.

## Close the program

- [ ] Every box above is checked with evidence.
- [ ] Report merged stack and lane receipts to the operator.

## Appendix A. Prototype evidence

Scroll and fractional move were validated in unit tests only this session. IME behavior stays unproven until PR3 lane 2 on MSI hardware.

## Appendix B. Alternatives rejected

Per-move `hyprctl` was rejected for latency. Position stays on uinput `EV_ABS`. Scroll uses `EV_REL` only.

## Appendix C. Risks

IME may need extra Quartz event types. uinput permissions on MSI can block live lanes. Both land in PR3 watch list.

## Appendix D. Links and reading list

Read `host/session.py` and `host/keys.py` before PR3. Use interrogate only if IME fix is contested after first live failure.
