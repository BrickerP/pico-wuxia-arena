// Native pointer events routed only to the selected emulator and its owned window.
// https://developer.apple.com/documentation/coregraphics/cgevent/posttopid(_:)
import AppKit
import CoreGraphics
import Foundation
struct Failure: Error, CustomStringConvertible { let description: String }
let args = Array(CommandLine.arguments.dropFirst())
func perform() throws {
    guard args.count == 5, let pid = Int32(args[0]), let requestedWindow = Int64(args[1]), requestedWindow > 0,
          let x = Double(args[3]), let y = Double(args[4]),
          x.isFinite, y.isFinite, ["move", "click"].contains(args[2]) else {
        throw Failure(description: "usage: native_emulator_pointer PID WINDOW_ID move|click X Y")
    }
    guard CGPreflightPostEventAccess(), let app = NSRunningApplication(processIdentifier: pid),
          app.executableURL?.lastPathComponent == "qemu-system-aarch64" else { throw Failure(description: "selected emulator or existing event access unavailable") }
    let point = CGPoint(x: x, y: y)
    let windows = CGWindowListCopyWindowInfo([.optionAll, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
    let owned = windows.first { window in
        guard (window[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid,
              (window[kCGWindowNumber as String] as? NSNumber)?.int64Value == requestedWindow,
              let box = window[kCGWindowBounds as String] as? [String: Any],
              let bx = box["X"] as? Double, let by = box["Y"] as? Double,
              let bw = box["Width"] as? Double, let bh = box["Height"] as? Double else { return false }
        return CGRect(x: bx, y: by, width: bw, height: bh).contains(point)
    }
    guard let owned, let windowID = (owned[kCGWindowNumber as String] as? NSNumber)?.int64Value else {
        throw Failure(description: "selected window is not owned by this emulator or point is outside its bounds; no event posted")
    }
    func event(_ type: CGEventType) throws -> CGEvent {
        guard let value = CGEvent(mouseEventSource: nil, mouseType: type, mouseCursorPosition: point, mouseButton: .left) else { throw Failure(description: "event allocation failed") }
        value.flags = []
        value.setIntegerValueField(.mouseEventWindowUnderMousePointer, value: windowID)
        value.setIntegerValueField(.mouseEventWindowUnderMousePointerThatCanHandleThisEvent, value: windowID)
        return value
    }
    try event(.mouseMoved).postToPid(pid)
    if args[2] == "click" {
        let up = try event(.leftMouseUp)
        defer { if !app.isTerminated { up.postToPid(pid) } }
        try event(.leftMouseDown).postToPid(pid)
        RunLoop.current.run(until: Date().addingTimeInterval(0.1))
    }
    print("POSTED delivery=process_targeted pid=\(pid) window=\(windowID) action=\(args[2]) x=\(x) y=\(y); observe actual result")
}
do { try perform() } catch { fputs("\(error)\n", stderr); exit(3) }
