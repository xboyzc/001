import Foundation
import ApplicationServices
import AppKit

let rootDir = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let postsPath = rootDir.appendingPathComponent("data/douyin_posts.json")
let visiblePostsPath = rootDir.appendingPathComponent("data/douyin_visible_posts.json")
let statePath = rootDir.appendingPathComponent("data/douyin_app_capture_state.json")

struct Post: Codable {
    let aweme_id: String
    let desc: String
    let create_time: Int?
    let share_url: String
    let duration_ms: Int?
    let play_url: String
    let download_url: String
    let music_url: String
    let image_urls: [String]
    let stats: [String: Int]?
    let raw_text_candidates: [String: String]
}

func writeJSON<T: Encodable>(_ value: T, to url: URL) throws {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
    let data = try encoder.encode(value)
    try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
    try data.write(to: url)
}

func attrString(_ element: AXUIElement, _ attr: String) -> String {
    var value: CFTypeRef?
    let error = AXUIElementCopyAttributeValue(element, attr as CFString, &value)
    if error != .success {
        return ""
    }
    if let string = value as? String {
        return string
    }
    if let number = value as? NSNumber {
        return number.stringValue
    }
    if let url = value as? URL {
        return url.absoluteString
    }
    return String(describing: value ?? "" as CFTypeRef)
}

func children(_ element: AXUIElement) -> [AXUIElement] {
    var value: CFTypeRef?
    let error = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &value)
    if error != .success {
        return []
    }
    return (value as? [AXUIElement]) ?? []
}

func cleanDescription(_ raw: String) -> String {
    var text = raw
    if let range = text.range(of: "妮可清醒局：") {
        text = String(text[range.upperBound...])
    } else if let range = text.range(of: "妮可清醒局于") {
        text = String(text[range.lowerBound...])
    }
    text = text.replacingOccurrences(of: #"Tag:\s*置顶\s*"#, with: "", options: .regularExpression)
    text = text.replacingOccurrences(of: #"\s+"#, with: " ", options: .regularExpression)
    let parts = text.components(separatedBy: " ")
    if parts.count > 8 {
        let half = parts.count / 2
        let left = parts.prefix(half).joined(separator: " ")
        let right = parts.suffix(parts.count - half).joined(separator: " ")
        if right.contains(left.prefix(min(12, left.count))) {
            text = left
        }
    }
    return text.trimmingCharacters(in: .whitespacesAndNewlines)
}

func countValue(_ token: String) -> Int? {
    let clean = token.trimmingCharacters(in: .whitespacesAndNewlines)
    if clean.hasSuffix("万") {
        let number = clean.dropLast()
        if let value = Double(number) {
            return Int(value * 10000)
        }
        return nil
    }
    return Int(clean)
}

func splitAppCardText(_ raw: String) -> (String, Int?) {
    var text = raw.trimmingCharacters(in: .whitespacesAndNewlines)
    if let range = text.range(of: "妮可清醒局：") {
        text = String(text[range.upperBound...])
    }
    text = text.replacingOccurrences(of: #"Tag:\s*置顶\s*"#, with: "", options: .regularExpression)
    text = text.replacingOccurrences(of: #"\s+"#, with: " ", options: .regularExpression)
    let pattern = #"^(.+?)\s+(\d+(?:\.\d+)?万|\d{1,12})\s+(.+)$"#
    guard let regex = try? NSRegularExpression(pattern: pattern) else {
        return (text, nil)
    }
    let range = NSRange(text.startIndex..<text.endIndex, in: text)
    guard let match = regex.firstMatch(in: text, range: range), match.numberOfRanges > 3,
          let leftRange = Range(match.range(at: 1), in: text),
          let countRange = Range(match.range(at: 2), in: text),
          let rightRange = Range(match.range(at: 3), in: text)
    else {
        return (text, nil)
    }
    let left = String(text[leftRange]).trimmingCharacters(in: .whitespacesAndNewlines)
    let right = String(text[rightRange]).trimmingCharacters(in: .whitespacesAndNewlines)
    let leftPrefix = String(left.prefix(min(18, left.count)))
    let rightPrefix = String(right.prefix(min(18, right.count)))
    if !leftPrefix.isEmpty && (right.hasPrefix(leftPrefix) || left.hasPrefix(rightPrefix)) {
        return (left, countValue(String(text[countRange])))
    }
    return (text, nil)
}

func videoId(from url: String) -> String? {
    let pattern = #"/video/(\d+)"#
    guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
    let range = NSRange(url.startIndex..<url.endIndex, in: url)
    guard let match = regex.firstMatch(in: url, range: range), match.numberOfRanges > 1 else { return nil }
    return Range(match.range(at: 1), in: url).map { String(url[$0]) }
}

func displayedPlayCount(from raw: String, cleaned: String) -> Int? {
    let (_, splitCount) = splitAppCardText(raw)
    if let splitCount {
        return splitCount
    }
    let clean = cleaned.trimmingCharacters(in: .whitespacesAndNewlines)
    guard clean.count >= 8 else { return nil }
    let prefix = String(clean.prefix(min(18, clean.count)))
    let escapedClean = NSRegularExpression.escapedPattern(for: clean)
    let escapedPrefix = NSRegularExpression.escapedPattern(for: prefix)
    let patterns = [
        "\(escapedClean)\\s+(\\d+(?:\\.\\d+)?万|\\d{1,12})\\s+\(escapedPrefix)",
        "\(escapedClean)\\s+(\\d+(?:\\.\\d+)?万|\\d{1,12})\\s*$",
    ]
    for pattern in patterns {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { continue }
        let range = NSRange(raw.startIndex..<raw.endIndex, in: raw)
        guard let match = regex.firstMatch(in: raw, range: range), match.numberOfRanges > 1 else { continue }
        if let valueRange = Range(match.range(at: 1), in: raw), let value = countValue(String(raw[valueRange])) {
            return value
        }
    }
    return nil
}

func collectPosts(from root: AXUIElement) -> ([Post], Int?) {
    var collected: [String: Post] = [:]
    var expectedCount: Int?

    func walk(_ element: AXUIElement, _ depth: Int) {
        if depth > 48 { return }
        let role = attrString(element, kAXRoleAttribute)
        let title = attrString(element, kAXTitleAttribute)
        let desc = attrString(element, kAXDescriptionAttribute)
        let value = attrString(element, kAXValueAttribute)
        let url = attrString(element, "AXURL")
        let combined = [title, desc, value, url].joined(separator: " ")

        if let match = combined.range(of: #"作品\s+(\d+)"#, options: .regularExpression) {
            let matchedText = String(combined[match])
            let digits = matchedText.filter { $0.isNumber }
            if let count = Int(digits), count > 0 {
                expectedCount = count
            }
        }

        if role == "AXLink", let id = videoId(from: url), desc.contains("妮可清醒局") {
            let shareURL = "https://www.douyin.com/video/\(id)"
            let split = splitAppCardText(desc)
            let cleaned = cleanDescription(split.0)
            let playCount = displayedPlayCount(from: desc, cleaned: cleaned)
            let post = Post(
                aweme_id: id,
                desc: cleaned,
                create_time: nil,
                share_url: shareURL,
                duration_ms: nil,
                play_url: "",
                download_url: "",
                music_url: "",
                image_urls: [],
                stats: playCount.map { ["play_count": $0] },
                raw_text_candidates: [
                    "source": "douyin_desktop_app_accessibility",
                    "app_url": url,
                    "app_description": desc,
                    "app_play_count": playCount.map(String.init) ?? "",
                ]
            )
            collected[id] = post
        }

        for child in children(element) {
            walk(child, depth + 1)
        }
    }

    walk(root, 0)
    let posts = collected.values.sorted { left, right in
        left.aweme_id > right.aweme_id
    }
    return (posts, expectedCount)
}

func findFirst(_ element: AXUIElement, _ depth: Int, matching: (AXUIElement, String) -> Bool) -> AXUIElement? {
    if depth > 48 { return nil }
    let role = attrString(element, kAXRoleAttribute)
    let title = attrString(element, kAXTitleAttribute)
    let desc = attrString(element, kAXDescriptionAttribute)
    let value = attrString(element, kAXValueAttribute)
    let url = attrString(element, "AXURL")
    let combined = [role, title, desc, value, url].joined(separator: " ")

    if matching(element, combined) {
        return element
    }

    for child in children(element) {
        if let found = findFirst(child, depth + 1, matching: matching) {
            return found
        }
    }
    return nil
}

func press(_ element: AXUIElement) -> Bool {
    AXUIElementPerformAction(element, kAXPressAction as CFString) == .success
}

func tryOpenWorksPage(processIdentifier: pid_t) {
    var root = AXUIElementCreateApplication(processIdentifier)
    if let mineLink = findFirst(root, 0, matching: { _, combined in
        combined.contains("AXLink") && (combined.contains("douyin.com/user/self") || combined.contains("我的"))
    }) {
        _ = press(mineLink)
        Thread.sleep(forTimeInterval: 3.0)
    }

    root = AXUIElementCreateApplication(processIdentifier)
    if let worksTab = findFirst(root, 0, matching: { _, combined in
        combined.contains("作品") && !combined.contains("/video/") && (combined.contains("AXButton") || combined.contains("AXRadioButton") || combined.contains("AXLink") || combined.contains("AXStaticText"))
    }) {
        _ = press(worksTab)
        Thread.sleep(forTimeInterval: 1.5)
    } else {
        Thread.sleep(forTimeInterval: 1.5)
    }
}

func readPreviousPosts() -> [Post] {
    guard let data = try? Data(contentsOf: visiblePostsPath) else { return [] }
    return (try? JSONDecoder().decode([Post].self, from: data)) ?? []
}

func writeState(ok: Bool, source: String, expectedCount: Int?, posts: [Post], message: String, fallback: Bool = false) {
    let state: [String: Any] = [
        "ok": ok,
        "source": source,
        "expectedCount": expectedCount as Any,
        "capturedCount": posts.count,
        "capturedIds": posts.map { $0.aweme_id },
        "fallback": fallback,
        "message": message,
        "capturedAt": ISO8601DateFormatter().string(from: Date()),
    ]

    if let stateData = try? JSONSerialization.data(withJSONObject: state, options: [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]) {
        try? FileManager.default.createDirectory(at: statePath.deletingLastPathComponent(), withIntermediateDirectories: true)
        try? stateData.write(to: statePath)
    }
}

guard let app = NSWorkspace.shared.runningApplications.first(where: { $0.bundleIdentifier == "com.bytedance.douyin.desktop" }) else {
    let state = ["ok": "false", "message": "抖音 App 未运行，请先打开抖音 App 并进入我的-作品页面。"]
    try? writeJSON(state, to: statePath)
    fputs("抖音 App 未运行，请先打开抖音 App。\n", stderr)
    exit(2)
}

app.activate(options: [.activateAllWindows])
Thread.sleep(forTimeInterval: 0.8)

var root = AXUIElementCreateApplication(app.processIdentifier)
var (posts, expectedCount) = collectPosts(from: root)

if posts.isEmpty {
    tryOpenWorksPage(processIdentifier: app.processIdentifier)
    root = AXUIElementCreateApplication(app.processIdentifier)
    (posts, expectedCount) = collectPosts(from: root)
}

if posts.isEmpty {
    let previousPosts = readPreviousPosts()
    if !previousPosts.isEmpty {
        writeState(
            ok: true,
            source: "douyin_desktop_app_accessibility_previous_success",
            expectedCount: nil,
            posts: previousPosts,
            message: "当前抖音 App 页面未读到作品，已沿用上一次成功抓取的作品列表继续刷新。",
            fallback: true
        )
        print("当前抖音 App 页面未读到作品，已沿用上一次成功抓取的 \(previousPosts.count) 条作品。")
        exit(0)
    }
    writeState(
        ok: false,
        source: "douyin_desktop_app_accessibility",
        expectedCount: expectedCount,
        posts: [],
        message: "没有从抖音 App 页面读到作品链接，请打开我的-作品页面后重试。"
    )
    fputs("没有从抖音 App 页面读到作品链接，请打开我的-作品页面后重试。\n", stderr)
    exit(3)
}

try writeJSON(posts, to: postsPath)
try writeJSON(posts, to: visiblePostsPath)
writeState(
    ok: true,
    source: "douyin_desktop_app_accessibility",
    expectedCount: expectedCount,
    posts: posts,
    message: "已从抖音 App 当前登录态页面抓取作品。"
)
print("Wrote \(posts.count) posts from Douyin App to \(visiblePostsPath.path)")
if let expected = expectedCount, expected != posts.count {
    print("Warning: page shows \(expected) works, captured \(posts.count). Scroll the Douyin App works page to the bottom and retry if needed.")
}
