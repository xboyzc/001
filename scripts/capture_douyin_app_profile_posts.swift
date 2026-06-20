import Foundation
import ApplicationServices
import AppKit

let rootDir = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let postsPath = rootDir.appendingPathComponent("data/douyin_posts.json")
let visiblePostsPath = rootDir.appendingPathComponent("data/douyin_visible_posts.json")
let statePath = rootDir.appendingPathComponent("data/douyin_app_profile_capture_state.json")

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
    let raw_text_candidates: [String: String]
}

func writeJSON<T: Encodable>(_ value: T, to url: URL) throws {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
    let data = try encoder.encode(value)
    try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
    try data.write(to: url)
}

func writeState(_ state: [String: Any]) {
    if let data = try? JSONSerialization.data(withJSONObject: state, options: [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]) {
        try? FileManager.default.createDirectory(at: statePath.deletingLastPathComponent(), withIntermediateDirectories: true)
        try? data.write(to: statePath)
    }
}

func attrString(_ element: AXUIElement, _ attr: String) -> String {
    var value: CFTypeRef?
    let error = AXUIElementCopyAttributeValue(element, attr as CFString, &value)
    if error != .success {
        return ""
    }
    if let string = value as? String { return string }
    if let number = value as? NSNumber { return number.stringValue }
    if let url = value as? URL { return url.absoluteString }
    return String(describing: value ?? "" as CFTypeRef)
}

func children(_ element: AXUIElement) -> [AXUIElement] {
    var value: CFTypeRef?
    let error = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute as CFString, &value)
    if error != .success { return [] }
    return (value as? [AXUIElement]) ?? []
}

func videoId(from url: String) -> String? {
    guard let regex = try? NSRegularExpression(pattern: #"/video/(\d+)"#) else { return nil }
    let range = NSRange(url.startIndex..<url.endIndex, in: url)
    guard let match = regex.firstMatch(in: url, range: range), match.numberOfRanges > 1 else { return nil }
    return Range(match.range(at: 1), in: url).map { String(url[$0]) }
}

func secUid(from text: String) -> String {
    if let range = text.range(of: #"sec_uid=([^&]+)"#, options: .regularExpression) {
        let part = String(text[range])
        return part.replacingOccurrences(of: "sec_uid=", with: "")
    }
    if let range = text.range(of: #"/user/([^/?#]+)"#, options: .regularExpression) {
        let part = String(text[range])
        return part.replacingOccurrences(of: "/user/", with: "")
    }
    return ""
}

func cleanDescription(_ raw: String, author: String) -> String {
    var text = raw
    if !author.isEmpty, let range = text.range(of: "\(author)：") {
        text = String(text[range.upperBound...])
    }
    text = text.replacingOccurrences(of: #"^\s*\d+\s+"#, with: "", options: .regularExpression)
    text = text.replacingOccurrences(of: #"\s+"#, with: " ", options: .regularExpression)
    let parts = text.components(separatedBy: " ")
    if parts.count > 4 {
        let half = parts.count / 2
        let left = parts.prefix(half).joined(separator: " ")
        let right = parts.suffix(parts.count - half).joined(separator: " ")
        if right.contains(left.prefix(min(10, left.count))) {
            text = left
        }
    }
    return text.trimmingCharacters(in: .whitespacesAndNewlines)
}

func walk(_ element: AXUIElement, _ depth: Int, _ visit: (AXUIElement) -> Void) {
    if depth > 48 { return }
    visit(element)
    for child in children(element) {
        walk(child, depth + 1, visit)
    }
}

let args = CommandLine.arguments.dropFirst()
let inputURL = args.first(where: { $0.hasPrefix("http") }) ?? ""
let limitIndex = CommandLine.arguments.firstIndex(of: "--limit")
let limit = limitIndex.flatMap { idx -> Int? in
    let next = CommandLine.arguments.index(after: idx)
    guard next < CommandLine.arguments.endIndex else { return nil }
    return Int(CommandLine.arguments[next])
} ?? 120
let targetSecUid = secUid(from: inputURL)

guard let app = NSWorkspace.shared.runningApplications.first(where: { $0.bundleIdentifier == "com.bytedance.douyin.desktop" }) else {
    writeState([
        "ok": false,
        "message": "抖音 App 未运行，无法使用已登录 App 抓取博主主页。",
        "capturedAt": ISO8601DateFormatter().string(from: Date()),
    ])
    fputs("抖音 App 未运行，无法使用已登录 App 抓取博主主页。\n", stderr)
    exit(2)
}

if !inputURL.isEmpty, let url = URL(string: inputURL), let appURL = app.bundleURL {
    let sema = DispatchSemaphore(value: 0)
    let config = NSWorkspace.OpenConfiguration()
    config.activates = true
    NSWorkspace.shared.open([url], withApplicationAt: appURL, configuration: config) { _, _ in
        sema.signal()
    }
    _ = sema.wait(timeout: .now() + 6)
}

app.activate(options: [.activateAllWindows])
Thread.sleep(forTimeInterval: 3.0)

var root = AXUIElementCreateApplication(app.processIdentifier)
var profileURL = ""
var authorName = ""
var expectedCount: Int?

for _ in 0..<8 {
    profileURL = ""
    authorName = ""
    expectedCount = nil
    walk(root, 0) { element in
        let title = attrString(element, kAXTitleAttribute)
        let desc = attrString(element, kAXDescriptionAttribute)
        let value = attrString(element, kAXValueAttribute)
        let url = attrString(element, "AXURL")
        let combined = [title, desc, value, url].joined(separator: " ")
        if profileURL.isEmpty, combined.contains("douyin.com/user/") {
            profileURL = combined
        }
        if authorName.isEmpty, !title.isEmpty, !["抖音", "作品", "推荐", "喜欢", "合集", "短剧"].contains(title), combined.contains("Value: 1") == false {
            if combined.contains("的抖音") == false && title.count <= 24 {
                authorName = title
            }
        }
        if let match = combined.range(of: #"作品\s+(\d+)"#, options: .regularExpression) {
            let digits = String(combined[match]).filter { $0.isNumber }
            if let count = Int(digits), count > 0 {
                expectedCount = max(expectedCount ?? 0, count)
            }
        }
    }
    let currentSecUid = secUid(from: profileURL)
    if targetSecUid.isEmpty || currentSecUid == targetSecUid {
        break
    }
    Thread.sleep(forTimeInterval: 1.5)
    root = AXUIElementCreateApplication(app.processIdentifier)
}

let currentSecUid = secUid(from: profileURL)
if let nameRange = profileURL.range(of: #"([^ ]+)的抖音\s*-\s*抖音"#, options: .regularExpression) {
    let matched = String(profileURL[nameRange])
    if let end = matched.range(of: "的抖音") {
        let parsedName = String(matched[..<end.lowerBound]).trimmingCharacters(in: .whitespacesAndNewlines)
        if !parsedName.isEmpty {
            authorName = parsedName
        }
    }
}
if !targetSecUid.isEmpty, currentSecUid != targetSecUid {
    writeState([
        "ok": false,
        "inputUrl": inputURL,
        "targetSecUid": targetSecUid,
        "currentSecUid": currentSecUid,
        "profileURL": profileURL,
        "message": "抖音 App 未成功打开目标博主主页，未更新作品库。",
        "capturedAt": ISO8601DateFormatter().string(from: Date()),
    ])
    fputs("抖音 App 未成功打开目标博主主页，未更新作品库。\n", stderr)
    exit(3)
}

var collected: [String: Post] = [:]
walk(root, 0) { element in
    let role = attrString(element, kAXRoleAttribute)
    let desc = attrString(element, kAXDescriptionAttribute)
    let url = attrString(element, "AXURL")
    guard role == "AXLink", let id = videoId(from: url) else { return }
    if !authorName.isEmpty, !desc.hasPrefix("\(authorName)：") {
        return
    }
    let post = Post(
        aweme_id: id,
        desc: cleanDescription(desc, author: authorName),
        create_time: nil,
        share_url: "https://www.douyin.com/video/\(id)",
        duration_ms: nil,
        play_url: "",
        download_url: "",
        music_url: "",
        image_urls: [],
        raw_text_candidates: [
            "source": "douyin_desktop_app_accessibility_profile",
            "app_url": url,
            "app_description": desc,
            "profile_url": profileURL,
            "author_name": authorName,
            "sec_uid": currentSecUid,
        ]
    )
    collected[id] = post
}

let posts = Array(collected.values)
    .sorted { $0.aweme_id > $1.aweme_id }
    .prefix(limit)

if posts.isEmpty {
    writeState([
        "ok": false,
        "inputUrl": inputURL,
        "targetSecUid": targetSecUid,
        "currentSecUid": currentSecUid,
        "profileURL": profileURL,
        "authorName": authorName,
        "expectedCount": expectedCount as Any,
        "capturedCount": 0,
        "message": "抖音 App 已打开目标主页，但没有读到作品链接。",
        "capturedAt": ISO8601DateFormatter().string(from: Date()),
    ])
    fputs("抖音 App 已打开目标主页，但没有读到作品链接。\n", stderr)
    exit(4)
}

try writeJSON(Array(posts), to: postsPath)
try writeJSON(Array(posts), to: visiblePostsPath)
writeState([
    "ok": true,
    "inputUrl": inputURL,
    "targetSecUid": targetSecUid,
    "currentSecUid": currentSecUid,
    "profileURL": profileURL,
    "authorName": authorName,
    "expectedCount": expectedCount as Any,
    "capturedCount": posts.count,
    "capturedIds": posts.map { $0.aweme_id },
    "message": "已从抖音 App 目标博主主页抓取公开作品。",
    "capturedAt": ISO8601DateFormatter().string(from: Date()),
])
print("Wrote \(posts.count) posts from Douyin App profile \(authorName) to \(visiblePostsPath.path)")
if let expected = expectedCount, expected != posts.count {
    print("Warning: page shows \(expected) works, captured \(posts.count).")
}
