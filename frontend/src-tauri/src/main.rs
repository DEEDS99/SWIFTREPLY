// SwiftReply — Tauri Desktop App (Windows + macOS + Linux)
// Handles: system tray, backend process management, deep links, notifications

#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{
    CustomMenuItem, Manager, SystemTray, SystemTrayEvent, SystemTrayMenu,
    SystemTrayMenuItem, WindowEvent,
};

// ── Backend process handle ─────────────────────────────────────────────────
struct BackendProcess(Mutex<Option<Child>>);

// ── Start bundled Python backend ───────────────────────────────────────────
fn start_backend(app_handle: &tauri::AppHandle) -> Option<Child> {
    let resource_path = app_handle
        .path_resolver()
        .resolve_resource("backend/swiftreply-backend")
        .unwrap_or_else(|| {
            app_handle
                .path_resolver()
                .resolve_resource("backend/swiftreply-backend.exe")
                .unwrap_or_default()
        });

    if resource_path.exists() {
        match Command::new(&resource_path)
            .env("PORT", "8000")
            .spawn()
        {
            Ok(child) => {
                println!("SwiftReply backend started (pid {})", child.id());
                return Some(child);
            }
            Err(e) => eprintln!("Failed to start backend: {e}"),
        }
    } else {
        // Dev mode: backend runs separately
        println!("Backend binary not found — assuming dev mode (backend runs separately)");
    }
    None
}

// ── System tray menu ───────────────────────────────────────────────────────
fn build_tray() -> SystemTray {
    let open = CustomMenuItem::new("open", "Open SwiftReply");
    let dashboard = CustomMenuItem::new("dashboard", "Live Dashboard");
    let conversations = CustomMenuItem::new("conversations", "Conversations");
    let separator = SystemTrayMenuItem::Separator;
    let quit = CustomMenuItem::new("quit", "Quit");

    let menu = SystemTrayMenu::new()
        .add_item(open)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(dashboard)
        .add_item(conversations)
        .add_native_item(separator)
        .add_item(quit);

    SystemTray::new().with_menu(menu)
}

// ── Tauri commands (callable from JS) ─────────────────────────────────────

#[tauri::command]
fn get_backend_url() -> String {
    std::env::var("SWIFTREPLY_API_URL")
        .unwrap_or_else(|_| "http://localhost:8000".to_string())
}

#[tauri::command]
fn get_app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[tauri::command]
fn show_notification(title: String, body: String) {
    // Handled by tauri notification plugin
    println!("Notification: {title} — {body}");
}

// ── Main ───────────────────────────────────────────────────────────────────

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .system_tray(build_tray())
        .on_system_tray_event(|app, event| match event {
            SystemTrayEvent::LeftClick { .. } => {
                if let Some(window) = app.get_window("main") {
                    window.show().ok();
                    window.set_focus().ok();
                }
            }
            SystemTrayEvent::MenuItemClick { id, .. } => match id.as_str() {
                "open" => {
                    if let Some(window) = app.get_window("main") {
                        window.show().ok();
                        window.set_focus().ok();
                    }
                }
                "dashboard" => {
                    if let Some(window) = app.get_window("main") {
                        window.show().ok();
                        window.eval("window.location.href='/dashboard'").ok();
                    }
                }
                "conversations" => {
                    if let Some(window) = app.get_window("main") {
                        window.show().ok();
                        window.eval("window.location.href='/conversations'").ok();
                    }
                }
                "quit" => {
                    // Kill backend before quitting
                    let state = app.state::<BackendProcess>();
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(mut child) = guard.take() {
                            child.kill().ok();
                        }
                    }
                    app.exit(0);
                }
                _ => {}
            },
            _ => {}
        })
        .setup(|app| {
            // Start bundled backend
            let child = start_backend(app.handle());
            let state = app.state::<BackendProcess>();
            *state.0.lock().unwrap() = child;

            // Hide from macOS dock if minimized to tray
            #[cfg(target_os = "macos")]
            app.set_activation_policy(tauri::ActivationPolicy::Regular);

            Ok(())
        })
        .on_window_event(|event| {
            // Minimize to tray instead of closing on X
            if let WindowEvent::CloseRequested { api, .. } = event.event() {
                let window = event.window();
                if window.label() == "main" {
                    window.hide().ok();
                    api.prevent_close();
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            get_backend_url,
            get_app_version,
            show_notification,
        ])
        .run(tauri::generate_context!())
        .expect("error while running SwiftReply desktop app");
}
