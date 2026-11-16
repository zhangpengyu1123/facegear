mod core;

use core::{solve, sweep, sweep2d, Params, SolveOut, Sweep2dOut, Sweep2dReq, SweepOut, SweepReq};

#[tauri::command]
fn solve_cmd(p: Params) -> SolveOut {
    solve(&p)
}

#[tauri::command]
fn sweep_cmd(req: SweepReq) -> SweepOut {
    sweep(&req)
}

#[tauri::command]
fn sweep2d_cmd(req: Sweep2dReq) -> Sweep2dOut {
    sweep2d(&req)
}

#[tauri::command]
fn version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            solve_cmd,
            sweep_cmd,
            sweep2d_cmd,
            version
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
