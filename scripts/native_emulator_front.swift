import AppKit
import ApplicationServices
import CoreGraphics
import Darwin

let arguments = Array(CommandLine.arguments.dropFirst())
guard arguments.count == 1, let pid = Int32(arguments[0]),
      let app = NSRunningApplication(processIdentifier: pid),
      app.executableURL?.lastPathComponent == "qemu-system-aarch64" else {
    fputs("Expected the selected live PICO emulator PID; nothing activated\n", stderr)
    exit(3)
}

// AXFrontmost alone can become true before a macOS Space transition has exposed
// any Qt windows. Do not report success until the selected viewport is drawable
// and is the actual focused window.
let windows = CGWindowListCopyWindowInfo(.optionAll, kCGNullWindowID) as? [[String: Any]] ?? []
let viewports = windows.filter {
    ($0[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid &&
        ($0[kCGWindowName as String] as? String)?.hasPrefix("PICO Emulator - ") == true
}
guard viewports.count == 1,
      let windowID = (viewports[0][kCGWindowNumber as String] as? NSNumber)?.uint32Value,
      let viewportTitle = viewports[0][kCGWindowName as String] as? String else {
    fputs("The selected emulator has no unique main viewport; nothing activated\n", stderr)
    exit(3)
}
if app.isHidden { _ = app.unhide() }
guard app.activate(options: [.activateAllWindows]) else {
    fputs("Could not request the selected emulator's windows\n", stderr)
    exit(3)
}
let target = AXUIElementCreateApplication(pid)
var writable: DarwinBoolean = false
guard AXUIElementIsAttributeSettable(target, kAXFrontmostAttribute as CFString, &writable) == .success,
      writable.boolValue,
      AXUIElementSetAttributeValue(target, kAXFrontmostAttribute as CFString, kCFBooleanTrue) == .success else {
    fputs("Could not activate the selected emulator\n", stderr)
    exit(3)
}
func title(of element: AXUIElement) -> String? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, kAXTitleAttribute as CFString, &value) == .success else { return nil }
    return value as? String
}
func viewportOnScreen() -> Bool {
    let current = CGWindowListCopyWindowInfo(.optionIncludingWindow, windowID) as? [[String: Any]] ?? []
    return current.contains {
        ($0[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid &&
            ($0[kCGWindowNumber as String] as? NSNumber)?.uint32Value == windowID &&
            $0[kCGWindowName as String] as? String == viewportTitle &&
            $0[kCGWindowIsOnscreen as String] as? Bool == true
    }
}
func focusedViewport() -> Bool {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(target, kAXFocusedWindowAttribute as CFString, &value) == .success,
          let value, CFGetTypeID(value) == AXUIElementGetTypeID() else { return false }
    let focused = unsafeBitCast(value, to: AXUIElement.self)
    var owner: pid_t = 0
    return AXUIElementGetPid(focused, &owner) == .success && owner == pid && title(of: focused) == viewportTitle
}
let deadline = Date().addingTimeInterval(5)
var raisedViewport = false
while !app.isTerminated && Date() < deadline {
    if NSWorkspace.shared.frontmostApplication?.processIdentifier == pid && viewportOnScreen() {
        if focusedViewport() {
            print("ACTIVATED selected emulator pid=\(pid) window=\(windowID) onscreen=true focused_title=\(viewportTitle)")
            exit(0)
        }
        if !raisedViewport {
            var value: CFTypeRef?
            if AXUIElementCopyAttributeValue(target, kAXWindowsAttribute as CFString, &value) == .success,
               let viewport = (value as? [AXUIElement])?.first(where: { title(of: $0) == viewportTitle }) {
                // The action result is not the proof; the next loop checks the
                // actual foreground, CG visibility and focused owner again.
                _ = AXUIElementPerformAction(viewport, kAXRaiseAction as CFString)
                raisedViewport = true
            }
        }
    }
    RunLoop.current.run(until: Date().addingTimeInterval(0.05))
}
fputs("Emulator viewport was not observed on screen and focused; no input sent\n", stderr)
exit(3)
