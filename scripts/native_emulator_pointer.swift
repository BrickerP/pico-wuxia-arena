// Moves target the selected emulator process. A trigger click requires its
// verified foreground viewport; process-only clicks did not trigger its UI.
// https://developer.apple.com/documentation/coregraphics/cgevent/posttopid(_:)
import AppKit
import ApplicationServices
import CoreGraphics
import Foundation
struct Failure: Error, CustomStringConvertible { let description: String }
let args = Array(CommandLine.arguments.dropFirst())
func perform() throws {
    guard [5, 8].contains(args.count), let pid = Int32(args[0]), let requestedWindow = Int64(args[1]), requestedWindow > 0,
          let x = Double(args[3]), let y = Double(args[4]),
          x.isFinite, y.isFinite, ["move", "click", "stroke"].contains(args[2]) else {
        throw Failure(description: "usage: native_emulator_pointer PID WINDOW_ID move|click X Y, or stroke X0 Y0 X1 Y1 0.1..1.0")
    }
    let stroke = args[2] == "stroke"
    guard args.count == (stroke ? 8 : 5) else { throw Failure(description: "wrong number of pointer arguments") }
    guard CGPreflightPostEventAccess(), let app = NSRunningApplication(processIdentifier: pid),
          app.executableURL?.lastPathComponent == "qemu-system-aarch64" else { throw Failure(description: "selected emulator or existing event access unavailable") }
    let point = CGPoint(x: x, y: y)
    var end = point
    var duration = 0.0
    if stroke {
        guard let endX = Double(args[5]), let endY = Double(args[6]), let seconds = Double(args[7]),
              endX.isFinite, endY.isFinite, seconds.isFinite, seconds >= 0.1, seconds <= 1.0 else {
            throw Failure(description: "stroke endpoints must be finite and duration must be 0.1..1.0 seconds")
        }
        end = CGPoint(x: endX, y: endY)
        duration = seconds
    }
    let windows = CGWindowListCopyWindowInfo([.optionAll, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
    let owned = windows.first { window in
        guard (window[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid,
              (window[kCGWindowNumber as String] as? NSNumber)?.int64Value == requestedWindow,
              let box = window[kCGWindowBounds as String] as? [String: Any],
              let bx = box["X"] as? Double, let by = box["Y"] as? Double,
              let bw = box["Width"] as? Double, let bh = box["Height"] as? Double else { return false }
        let bounds = CGRect(x: bx, y: by, width: bw, height: bh)
        return bounds.contains(point) && bounds.contains(end)
    }
    guard let owned, let windowID = (owned[kCGWindowNumber as String] as? NSNumber)?.int64Value else {
        throw Failure(description: "selected window is not owned by this emulator or point is outside its bounds; no event posted")
    }
    let click = args[2] == "click"
    if click {
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid,
              !CGEventSource.buttonState(.combinedSessionState, button: .left) else {
            throw Failure(description: "click needs the foreground emulator with no physical button held")
        }
        var focused: CFTypeRef?
        let application = AXUIElementCreateApplication(pid)
        guard AXUIElementCopyAttributeValue(application, kAXFocusedWindowAttribute as CFString, &focused) == .success,
              let focused, CFGetTypeID(focused) == AXUIElementGetTypeID() else {
            throw Failure(description: "focused emulator window unavailable; no click posted")
        }
        var title: CFTypeRef?
        let focusedWindow = unsafeBitCast(focused, to: AXUIElement.self)
        guard AXUIElementCopyAttributeValue(focusedWindow, kAXTitleAttribute as CFString, &title) == .success,
              let title = title as? String, title.hasPrefix("PICO Emulator - ") else {
            throw Failure(description: "click needs the main emulator viewport, not its settings")
        }
        var hit: AXUIElement?
        var owner: pid_t = 0
        guard AXUIElementCopyElementAtPosition(AXUIElementCreateSystemWide(), Float(x), Float(y), &hit) == .success,
              let hit, AXUIElementGetPid(hit, &owner) == .success, owner == pid else {
            throw Failure(description: "click point is covered by another app; no click posted")
        }
    }
    func event(_ type: CGEventType, at position: CGPoint) throws -> CGEvent {
        guard let value = CGEvent(mouseEventSource: nil, mouseType: type, mouseCursorPosition: position, mouseButton: .left) else { throw Failure(description: "event allocation failed") }
        value.flags = []
        value.setIntegerValueField(.mouseEventWindowUnderMousePointer, value: windowID)
        value.setIntegerValueField(.mouseEventWindowUnderMousePointerThatCanHandleThisEvent, value: windowID)
        return value
    }
    if stroke {
        let steps = Int(ceil(duration * 90))
        let began = Date()
        for index in 0...steps {
            guard !app.isTerminated else { throw Failure(description: "selected emulator exited during stroke") }
            let fraction = Double(index) / Double(steps)
            let deadline = began.addingTimeInterval(duration * fraction)
            while Date() < deadline { RunLoop.current.run(until: min(deadline, Date().addingTimeInterval(0.005))) }
            let eased = fraction * fraction * fraction * (10 + fraction * (-15 + 6 * fraction))
            let position = CGPoint(x: point.x + (end.x - point.x) * eased, y: point.y + (end.y - point.y) * eased)
            try event(.mouseMoved, at: position).postToPid(pid)
        }
        print("POSTED delivery=process_targeted pid=\(pid) window=\(windowID) action=stroke samples=\(steps + 1) seconds=\(duration); verify SDK trajectory separately")
        return
    }
    if click { try event(.mouseMoved, at: point).post(tap: .cghidEventTap) }
    else { try event(.mouseMoved, at: point).postToPid(pid) }
    if click {
        // Publish the hover ray before the trigger consumes it.
        RunLoop.current.run(until: Date().addingTimeInterval(0.1))
        let up = try event(.leftMouseUp, at: point)
        defer { up.post(tap: .cghidEventTap) }
        try event(.leftMouseDown, at: point).post(tap: .cghidEventTap)
        RunLoop.current.run(until: Date().addingTimeInterval(0.1))
    }
    print("POSTED delivery=\(click ? "foreground_hid" : "process_targeted") pid=\(pid) window=\(windowID) action=\(args[2]) x=\(x) y=\(y); observe actual result")
}
do { try perform() } catch { fputs("\(error)\n", stderr); exit(3) }
