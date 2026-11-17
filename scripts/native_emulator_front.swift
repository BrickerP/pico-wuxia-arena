import AppKit
import Darwin

let arguments = Array(CommandLine.arguments.dropFirst())
guard arguments.count == 1, let pid = Int32(arguments[0]),
      let app = NSRunningApplication(processIdentifier: pid),
      app.executableURL?.lastPathComponent == "qemu-system-aarch64" else {
    fputs("Expected the selected live PICO emulator PID; nothing activated\n", stderr)
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
let deadline = Date().addingTimeInterval(2)
while NSWorkspace.shared.frontmostApplication?.processIdentifier != pid && Date() < deadline {
    RunLoop.current.run(until: Date().addingTimeInterval(0.05))
}
guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
    fputs("Emulator foreground was not observed\n", stderr)
    exit(3)
}
print("ACTIVATED selected emulator pid=\(pid)")
