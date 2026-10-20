mod capture;
mod desk;

use capture::{cursor_hidden, step, Event, Phase};
use desk::Edge;

fn main() {
    let mut phase = Phase::Local;
    println!("span-kvm desk");
    for landing in desk::msi_desk() {
        println!("  {:?} -> {},{}", landing.edge, landing.x, landing.y);
    }
    phase = step(phase, Event::Crossed);
    println!(
        "after cross: {phase:?}, hidden={}",
        cursor_hidden(phase)
    );
    phase = step(phase, Event::PeerGone);
    println!(
        "peer gone before ack: {phase:?}, hidden={}",
        cursor_hidden(phase)
    );
    let right = desk::landing(Edge::Right);
    println!("right landing {},{}", right.x, right.y);
}
