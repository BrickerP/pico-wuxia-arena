// Real macOS keyboard input into the selected PICO Emulator, never application pose injection.
import AppKit
import CoreGraphics
import Carbon.HIToolbox
import Foundation

struct InputFailure: Error, CustomStringConvertible { let description: String }
let args = Array(CommandLine.arguments.dropFirst())
guard args.count >= 3, let pid = Int32(args[0]), let duration = Double(args[2]),
      duration >= 0.05, duration <= 0.5 else {
    fputs("usage: native_emulator_hold_key PID w|a|s|d|q|e 0.05..0.5 [--plain] [--dry-run]\n", stderr)
    exit(2)
}
let keys: [String: Int] = ["w": kVK_ANSI_W, "a": kVK_ANSI_A, "s": kVK_ANSI_S,
                           "d": kVK_ANSI_D, "q": kVK_ANSI_Q, "e": kVK_ANSI_E]
let shifted = !args.contains("--plain")
guard args.dropFirst(3).allSatisfy({ ["--plain", "--dry-run"].contains($0) }) else {
    fputs("unsupported option\n", stderr); exit(2)
}
func perform() throws {
    guard let key = keys[args[1].lowercased()] else { throw InputFailure(description: "unsupported movement key") }
    guard let app = NSRunningApplication(processIdentifier: pid),
          app.executableURL?.lastPathComponent == "qemu-system-aarch64" else {
        throw InputFailure(description: "selected PID is not the live emulator")
    }
    guard CGPreflightPostEventAccess() else { throw InputFailure(description: "existing macOS event-post access unavailable") }
    if args.contains("--dry-run") { print("READY pid=\(pid) key=\(args[1]) shifted=\(shifted) seconds=\(duration); no input posted"); return }
    guard CGEventSource.flagsState(.combinedSessionState).intersection([.maskShift, .maskControl, .maskAlternate, .maskCommand]).isEmpty,
          !CGEventSource.keyState(.combinedSessionState, key: CGKeyCode(key)) else {
        throw InputFailure(description: "movement key or modifiers currently down; no input posted")
    }
    if NSWorkspace.shared.frontmostApplication?.processIdentifier != pid {
        app.unhide()
        _ = app.activate(options: [.activateAllWindows])
    }
    let deadline = Date().addingTimeInterval(2)
    while NSWorkspace.shared.frontmostApplication?.processIdentifier != pid && Date() < deadline {
        RunLoop.current.run(until: Date().addingTimeInterval(0.02))
    }
    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else { throw InputFailure(description: "emulator foreground could not be confirmed") }
    func event(_ code: Int, _ down: Bool, _ flags: CGEventFlags) throws -> CGEvent {
        guard let value = CGEvent(keyboardEventSource: nil, virtualKey: CGKeyCode(code), keyDown: down) else {
            throw InputFailure(description: "keyboard event allocation failed")
        }
        value.flags = flags
        return value
    }
    let flags: CGEventFlags = shifted ? [.maskShift] : []
    let up = try event(key, false, flags)
    let shiftDown = try event(kVK_Shift, true, [.maskShift])
    let shiftUp = try event(kVK_Shift, false, [])
    var modifierPosted = false, keyPosted = false
    defer {
        if keyPosted { up.post(tap: .cghidEventTap) }
        if modifierPosted { shiftUp.post(tap: .cghidEventTap) }
        RunLoop.current.run(until: Date().addingTimeInterval(0.02))
    }
    if shifted { shiftDown.post(tap: .cghidEventTap); modifierPosted = true }
    try event(key, true, flags).post(tap: .cghidEventTap); keyPosted = true
    let until = Date().addingTimeInterval(duration)
    while Date() < until {
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else { throw InputFailure(description: "foreground changed; releasing keys") }
        RunLoop.current.run(until: min(until, Date().addingTimeInterval(0.01)))
    }
    print("POSTED pid=\(pid) key=\(args[1]) shifted=\(shifted) seconds=\(duration); verify SDK trajectory separately")
}
do { try perform() } catch { fputs("\(error)\n", stderr); exit(3) }
