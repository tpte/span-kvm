/// Local pointer policy.
///
/// Lan Mouse hides the cursor inside the event tap as soon as the edge is
/// crossed, and a later DTLS timeout does not undo that. Span stays Local
/// until the peer acks, and any drop returns to Local.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Phase {
    Local,
    Waiting,
    Remote,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Event {
    Crossed,
    Ack,
    PeerGone,
    Release,
}

pub fn step(phase: Phase, event: Event) -> Phase {
    match (phase, event) {
        (Phase::Local, Event::Crossed) => Phase::Waiting,
        (Phase::Waiting, Event::Ack) => Phase::Remote,
        (Phase::Waiting, Event::PeerGone | Event::Release) => Phase::Local,
        (Phase::Remote, Event::PeerGone | Event::Release) => Phase::Local,
        (phase, _) => phase,
    }
}

/// The Mac cursor may be hidden only while the peer is actually driving it.
pub fn cursor_hidden(phase: Phase) -> bool {
    phase == Phase::Remote
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn no_ack_does_not_hide_the_cursor() {
        let phase = step(Phase::Local, Event::Crossed);
        assert_eq!(phase, Phase::Waiting);
        assert!(!cursor_hidden(phase));
        let phase = step(phase, Event::PeerGone);
        assert_eq!(phase, Phase::Local);
    }

    #[test]
    fn drop_after_ack_returns_home() {
        let phase = step(step(Phase::Local, Event::Crossed), Event::Ack);
        assert!(cursor_hidden(phase));
        assert_eq!(step(phase, Event::PeerGone), Phase::Local);
    }
}
