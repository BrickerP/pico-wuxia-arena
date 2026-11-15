// Native macOS pointer events for the explicitly selected PICO Emulator only.
import AppKit
import ApplicationServices
import CoreGraphics
import Foundation
struct Failure: Error, CustomStringConvertible { let description: String }
let args = Array(CommandLine.arguments.dropFirst())
func perform() throws {
    guard args.count == 4, let pid = Int32(args[0]), let x = Double(args[2]), let y = Double(args[3]),
          x.isFinite, y.isFinite, ["move", "click"].contains(args[1]) else {
        throw Failure(description: "usage: native_emulator_pointer PID move|click X Y")
    }
    guard CGPreflightPostEventAccess(), let app = NSRunningApplication(processIdentifier: pid),
          app.executableURL?.lastPathComponent == "qemu-system-aarch64" else { throw Failure(description: "selected emulator or existing event access unavailable") }
    if NSWorkspace.shared.frontmostApplication?.processIdentifier != pid {
        app.unhide()
        _ = app.activate(options: [.activateAllWindows])
    }
    let deadline = Date().addingTimeInterval(2)
    while NSWorkspace.shared.frontmostApplication?.processIdentifier != pid && Date() < deadline {
        RunLoop.current.run(until: Date().addingTimeInterval(0.02))
    }
    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else { throw Failure(description: "emulator foreground unconfirmed") }
    let point = CGPoint(x: x, y: y)
    var hit: AXUIElement?
    let result = AXUIElementCopyElementAtPosition(AXUIElementCreateSystemWide(), Float(x), Float(y), &hit)
    var owner: pid_t = 0
    guard result == .success, let element = hit, AXUIElementGetPid(element, &owner) == .success, owner == pid else {
        throw Failure(description: "system accessibility hit-test owner=\(owner) status=\(result.rawValue); selected emulator not hit, no event posted")
    }
    func event(_ type: CGEventType) throws -> CGEvent {
        guard let value = CGEvent(mouseEventSource: nil, mouseType: type, mouseCursorPosition: point, mouseButton: .left) else { throw Failure(description: "event allocation failed") }
        return value
    }
    try event(.mouseMoved).post(tap: .cghidEventTap)
    if args[1] == "click" {
        let up = try event(.leftMouseUp)
        defer { up.post(tap: .cghidEventTap) }
        try event(.leftMouseDown).post(tap: .cghidEventTap)
        RunLoop.current.run(until: Date().addingTimeInterval(0.1))
    }
    print("POSTED pid=\(pid) action=\(args[1]) x=\(x) y=\(y); observe actual result")
}
do { try perform() } catch { fputs("\(error)\n", stderr); exit(3) }
