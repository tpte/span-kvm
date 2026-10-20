/// One Linux host can own more than one edge of the Mac.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Edge {
    Left,
    Right,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Landing {
    pub edge: Edge,
    pub x: i32,
    pub y: i32,
}

/// MSI laptop on the left of the Mac, BenQ on the right.
/// Coordinates are Hyprland logical pixels: eDP-2 is 1280 wide at scale 1.5,
/// HDMI-A-1 starts at x=1280.
pub fn msi_desk() -> [Landing; 2] {
    [
        Landing {
            edge: Edge::Left,
            x: 1240,
            y: 360,
        },
        Landing {
            edge: Edge::Right,
            x: 1320,
            y: 540,
        },
    ]
}

pub fn landing(edge: Edge) -> Landing {
    msi_desk()
        .into_iter()
        .find(|item| item.edge == edge)
        .expect("every edge has a landing")
}
