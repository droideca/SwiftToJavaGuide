"""Source of truth for the Swift -> Java mapping dataset.

Derived from "Swift to Java.md" (Java 21 baseline). Run this file to regenerate
src/main/resources/data/mappings.json. Every entry is hand-written; `detect`
holds Swift-side regexes used by POST /api/analyze.
"""
import json, re, sys, pathlib

GUIDE = {
    "title": "Swift to Java Conversion Guide",
    "version": "1.0.0",
    "javaBaseline": "21",
    "description": "Practical, deterministic mappings for converting Swift code and Swift habits into idiomatic Java 21.",
}

CATEGORIES = [
    ("mindset", "Mindset shifts", "The big conceptual differences: memory, null-safety, value types, defaults."),
    ("data-types", "Data types", "Primitives, overflow, boxing, optionals, tuples, enums and structs."),
    ("strings", "String handling", "Equality, interpolation, text blocks, UTF-16 length, method mapping."),
    ("lambdas", "Lambdas and closures", "Lambda syntax, capture rules, functional interfaces, method references."),
    ("control-flow", "Control flow", "if/guard, pattern matching, switch, loops, defer."),
    ("objects", "Objects and initialization", "Classes, properties, lifecycle, statics, constructors, concurrency basics."),
    ("oop", "Encapsulation and inheritance", "Access modifiers, scope, inheritance, interfaces, extensions, generics."),
    ("exceptions", "Exception handling", "Checked vs unchecked, throwing, catching, try?/try!, resources."),
    ("collections", "Arrays and collections", "Reference semantics, collection types, immutability, common operations."),
    ("streams", "Streams", "map/filter/reduce chains, collectors, comparators."),
    ("functions", "Functions", "Static methods, labels, overloading, varargs, inout, generics."),
    ("testing", "Unit tests", "XCTest / Swift Testing to JUnit Jupiter."),
]

M = []

def E(id, category, title, swift, java, summary, risk, detect=(), swift_example=None,
      java_example=None, gotchas=(), related=(), tags=(), since=None):
    M.append({
        "id": id, "category": category, "title": title, "swift": swift, "java": java,
        "summary": summary, "risk": risk, "detect": list(detect),
        "swiftExample": swift_example, "javaExample": java_example,
        "gotchas": list(gotchas), "related": list(related), "tags": list(tags),
        "since": since,
    })

# ---------------------------------------------------------------- mindset
E("arc-vs-gc", "mindset", "ARC → garbage collector",
  "weak / unowned / ARC", "garbage collector (no equivalent needed)",
  "Java uses a tracing garbage collector, so reference cycles do not leak and there is no weak/unowned bookkeeping.",
  "low", [r"\b(weak|unowned)\s+(var|let)\b"],
  "weak var delegate: Delegate?",
  "private Delegate delegate;   // plain reference; cycles are collected by the GC",
  ["There is no deinit; use AutoCloseable + try-with-resources for deterministic cleanup.",
   "java.lang.ref.WeakReference exists but is for caches, not for breaking delegate cycles."],
  ["deinit-autocloseable", "weak-self-capture"], ["memory"])

E("open-by-default", "mindset", "Classes are open by default",
  "final class (closed by default for public)", "final class (open by default)",
  "Java classes and methods can be subclassed/overridden unless marked final, the opposite of Swift's public default.",
  "medium", [],
  "public final class Money { }",
  "public final class Money { }   // add final deliberately",
  ["Mark classes not designed for inheritance as final.",
   "let → final is also opt-in: Java locals and fields are mutable unless you write final."],
  ["access-modifiers", "let-var"], ["inheritance"])

# ---------------------------------------------------------------- data types
E("let-var", "data-types", "let / var → final / var",
  "let x = …  /  var x = …", "final var x = …  /  var x = …",
  "Swift let maps to final; Java's var keyword is only type inference and works only for local variables.",
  "low", [r"^[ \t]*(let|var)[ \t]+\w+[ \t]*(:[^=\n]+)?="],
  "let count = 42\nvar total = 0",
  "final var count = 42;   // or: final int count = 42;\nvar total = 0;          // int",
  ["Java var is NOT mutability: it means 'infer the type'. Use final for immutability.",
   "var works only for local variables, never for fields, parameters or return types."],
  ["open-by-default"], ["variables", "inference"])

E("int-width", "data-types", "Int → long (or int)",
  "Int (64-bit)", "long (64-bit) or int (32-bit)",
  "Swift Int is 64-bit on modern platforms; Java int is 32-bit. Pick int or long deliberately based on value range.",
  "medium", [r"\bInt(64|32|16|8)?\b(?!\()"],
  "let count: Int = 42",
  "final long count = 42L;   // or int, if the range allows",
  ["Int32 → int, Int16 → short, Int8 → byte (byte is signed: -128…127).",
   "long literals need an L suffix when they exceed int range: 3_000_000_000L."],
  ["integer-overflow", "unsigned-types", "boxed-types"], ["primitives", "numbers"])

E("unsigned-types", "data-types", "UInt types → no unsigned types",
  "UInt, UInt8, UInt16, UInt32, UInt64", "(none) — use a wider signed type",
  "Java has no unsigned integer types; use a wider type or helpers like Integer.toUnsignedString and Byte.toUnsignedInt.",
  "medium", [r"\bUInt(8|16|32|64)?\b"],
  "let flags: UInt8 = 0xFF",
  "int flags = 0xFF;                       // widen\nint unsigned = Byte.toUnsignedInt(b);   // read a byte as 0…255",
  ["byte b = (byte) 0xFF is -1, not 255."], ["int-width"], ["primitives", "numbers"])

E("float-literal", "data-types", "Float → float (needs f suffix)",
  "Float / Double", "float / double",
  "Double maps to double. Float maps to float, and float literals need an f suffix.",
  "low", [r"\bFloat\b"],
  "let ratio: Float = 1.5",
  "final float ratio = 1.5f;",
  ["1.5 without f is a double literal and will not compile into a float variable."],
  ["int-width"], ["primitives", "numbers"])

E("character-utf16", "data-types", "Character → char (UTF-16 code unit)",
  "Character (grapheme cluster)", "char (UTF-16 code unit) / int code point",
  "A Java char is a single UTF-16 code unit, not a user-perceived character. Emoji and many symbols need two chars.",
  "medium", [r"\bCharacter\b"],
  "let c: Character = \"👍\"",
  "String c = \"👍\";          // a char cannot hold it\nint cp = c.codePointAt(0);",
  ["Use code points (String.codePoints()) when you need real characters."],
  ["string-length"], ["primitives", "unicode"])

E("integer-overflow", "data-types", "Overflow traps → overflow silently wraps",
  "Overflow traps at runtime; &+ wraps", "Overflow silently wraps; Math.addExact throws",
  "Swift traps on integer overflow. Java silently wraps around, so use Math.*Exact where overflow would be a bug.",
  "high", [r"&[+\-*]", r"\bInt(32|64)?\.(max|min)\b", r"addingReportingOverflow"],
  "let x = Int32.max\nlet y = x + 1   // traps",
  "int x = Integer.MAX_VALUE;\nx = x + 1;                         // -2147483648, no error!\nint safe = Math.addExact(a, b);    // throws ArithmeticException",
  ["Math.addExact, subtractExact, multiplyExact, toIntExact all throw on overflow."],
  ["int-width"], ["numbers", "safety"])

E("boxed-types", "data-types", "Generics need boxed types (Integer, Long…)",
  "[Int], Int? (no boxing concept)", "List<Integer>, Integer (wrapper classes)",
  "Collections and generics can't hold primitives, so Java auto-boxes int → Integer etc. Boxed values compare by reference with == and NPE when unboxing null.",
  "high", [r"\[\s*(Int|Double|Bool|Float|Int64|Int32)\s*\]", r"\b(Int|Double|Bool)\?"],
  "let ids: [Int] = [1000]\nlet a: Int? = nil",
  "Integer a = 1000, b = 1000;\na == b;          // false! compares references\na.equals(b);     // true\n\nInteger maybe = null;\nint n = maybe;   // NullPointerException on unboxing",
  ["Always compare wrappers with equals() or Objects.equals().",
   "List<int> is not allowed; write List<Integer>."],
  ["equality-operator", "int-width"], ["primitives", "generics", "equality"])

E("optional-type", "data-types", "Optional type T? → nullable reference",
  "String?", "String (may be null) / Optional<String> as return type",
  "Any Java reference may be null; the type system won't help. Decide an explicit null strategy for every Swift optional.",
  "high", [r":\s*[A-Z][\w<>\[\]\., ]*\?(?![?.])", r"\bnil\b"],
  "var name: String? = nil",
  "String name = null;   // nothing in the type says this can be null",
  ["Non-optional Swift values have no Java guarantee either: fields default to null.",
   "Convention: Optional<T> mainly as a return type, not for fields or parameters."],
  ["optional-binding", "nil-coalescing", "optional-chaining", "force-unwrap", "optional-return"],
  ["optionals", "null-safety"])

E("optional-binding", "data-types", "if let / guard let → null check",
  "if let x { } / guard let x else { return }", "if (x != null) { } / if (x == null) return;",
  "Optional binding becomes an explicit null check; guard let becomes an early return.",
  "medium", [r"\b(if|guard|while)\s+(let|var)\b"],
  "guard let user = user else { return }\nif let name { print(name) }",
  "if (user == null) {\n    return;\n}\nif (name != null) { System.out.println(name); }",
  ["`if let x = x` shadows; in Java just reuse the variable — redeclaring a local is a compile error.",
   "For Optional<T> values: x.ifPresent(v -> …)."],
  ["optional-type", "variable-shadowing", "type-cast-binding"], ["optionals", "null-safety", "control-flow"])

E("nil-coalescing", "data-types", "?? → requireNonNullElse / orElse",
  "x ?? fallback", "Objects.requireNonNullElse(x, fallback) / opt.orElse(fallback)",
  "Nil-coalescing becomes a ternary, Objects.requireNonNullElse, or Optional.orElse / orElseGet.",
  "low", [r"\?\?"],
  "let display = name ?? \"Unknown\"",
  "String display = Objects.requireNonNullElse(name, \"Unknown\");\n// Optional: findUser(id).map(User::name).orElse(\"Unknown\");",
  ["orElse(expr) always evaluates expr; use orElseGet(() -> expr) for expensive fallbacks."],
  ["optional-type", "optional-return"], ["optionals"])

E("optional-chaining", "data-types", "Optional chaining x?.y → null checks / Optional.map",
  "user?.address?.city", "Optional.ofNullable(user).map(User::address).map(Address::city)",
  "There is no ?. operator. Use explicit null checks or chain Optional.map.",
  "medium", [r"\w\?\.\w"],
  "let city = user?.address?.city",
  "String city = Optional.ofNullable(user)\n        .map(User::address)\n        .map(Address::city)\n        .orElse(null);",
  ["Calling a method on null throws NullPointerException; nothing short-circuits automatically."],
  ["optional-type", "method-references"], ["optionals", "null-safety"])

E("force-unwrap", "data-types", "Force unwrap x! → orElseThrow / requireNonNull",
  "x!", "opt.orElseThrow() / Objects.requireNonNull(x)",
  "Force unwrap becomes orElseThrow() on Optional, or Objects.requireNonNull for plain references.",
  "medium", [r"[\w)\]]!(?=[\s.)\],;]|$)"],
  "let user = findUser(id)!",
  "User user = findUser(id).orElseThrow();\nUser u2 = Objects.requireNonNull(maybeUser, \"user\");",
  ["Dereferencing null already throws NPE, but requireNonNull fails earlier with a clearer message."],
  ["optional-type"], ["optionals"])

E("optional-return", "data-types", "Function returning T? → Optional<T>",
  "func findUser(id: String) -> User?", "Optional<User> findUser(String id)",
  "By convention Java uses Optional<T> mainly for return values that may be absent.",
  "medium", [r"->\s*[\w<>\[\]\.]+\?\s*(\{|$|where)"],
  "func findUser(id: String) -> User?",
  "Optional<User> findUser(String id) { ... }\n\nString display = findUser(id)\n        .map(User::name)\n        .orElse(\"Unknown\");",
  ["x?.foo → x.map(X::foo); x ?? y → x.orElse(y); x! → x.orElseThrow(); x == nil → x.isEmpty().",
   "Never return null from a method declared to return Optional."],
  ["optional-type", "failable-init"], ["optionals", "api-design"])

E("tuples", "data-types", "Tuples → record",
  "(min: Int, max: Int)", "record MinMax(int min, int max) {}",
  "Java has no tuples. Declare a small record for multiple return values.",
  "medium", [r"->\s*\(\s*\w+\s*:", r"->\s*\(\s*[A-Z]\w*\s*,"],
  "func minMax() -> (min: Int, max: Int)",
  "record MinMax(int min, int max) {}\nMinMax minMax() { ... }",
  ["Map.entry(k, v) is a common stand-in for ad-hoc pairs."],
  ["struct-to-record"], ["records"])

E("simple-enum", "data-types", "enum → enum (with fields and methods)",
  "enum Planet { case mercury, earth }", "enum Planet { MERCURY, EARTH }",
  "Simple enums map directly; Java enum constants are UPPER_SNAKE_CASE and can carry fields, constructors and methods.",
  "low", [r"^[ \t]*(\w+[ \t]+)*enum[ \t]+\w+"],
  "enum Planet: Double {\n    case mercury = 3.303e23, earth = 5.976e24\n}",
  "enum Planet {\n    MERCURY(3.303e23), EARTH(5.976e24);\n\n    private final double mass;\n    Planet(double mass) { this.mass = mass; }\n    double mass() { return mass; }\n}",
  ["Raw values become constructor arguments + a field.",
   "Enums with associated values need a sealed interface instead."],
  ["enum-associated-values", "switch-arrow"], ["enums"])

E("enum-associated-values", "data-types", "Enum with associated values → sealed interface + records",
  "enum Shape { case circle(radius: Double) }", "sealed interface Shape permits Circle, Rect {}",
  "Each case with associated values becomes a record implementing a sealed interface; switch over it exhaustively.",
  "medium", [r"^[ \t]*case[ \t]+\w+[ \t]*\("],
  "enum Shape {\n    case circle(radius: Double)\n    case rect(w: Double, h: Double)\n}",
  "sealed interface Shape permits Circle, Rect {}\nrecord Circle(double radius) implements Shape {}\nrecord Rect(double w, double h) implements Shape {}",
  ["Pattern-matching switch (Java 21) is exhaustive over sealed types, so no default branch is needed."],
  ["switch-patterns", "sealed-hierarchies", "simple-enum"], ["enums", "sealed", "records"], "Java 21")

E("struct-to-record", "data-types", "struct → record (reference type!)",
  "struct Point { let x: Int; let y: Int }", "record Point(int x, int y) {}",
  "Structs usually become records: immutable, with generated equals/hashCode/toString. Records are still references; value semantics come from immutability, not copying.",
  "high", [r"\bstruct\s+\w+"],
  "struct Point { let x: Int; let y: Int }\nvar b = a; b.x = 5   // a unchanged",
  "record Point(int x, int y) {}\nPoint b = a;           // same object, no copy\nPoint moved = new Point(5, a.y());   // 'mutate' by creating a new one",
  ["Mutable structs have no Java equivalent: copy explicitly or make the type immutable.",
   "Record accessors have no get prefix: point.x().",
   "Validate in a compact constructor: record Range(int lo, int hi) { Range { if (lo > hi) throw … } }"],
  ["tuples", "equatable-hashable", "collection-types"], ["records", "value-semantics"])

# ---------------------------------------------------------------- strings
E("equality-operator", "strings", "String/object equality: == → .equals()",
  "a == b (value equality)", "a.equals(b) / Objects.equals(a, b)",
  "In Java, == compares references for objects (including String and Integer). Use equals() for value equality. This is the #1 bug for Swift developers.",
  "high", [r"[^=!<>]==[^=]", r"!=(?!=)"],
  "if input == \"hi\" { }",
  "String a = \"hi\";\nString b = new String(\"hi\");\na == b;               // false: compares references\na.equals(b);          // true\n\"hi\".equals(input);   // null-safe idiom\nObjects.equals(a, b); // null-safe for both",
  ["== is fine for primitives (int, double, boolean) and enum constants.",
   "Arrays: a.equals(b) also compares references; use Arrays.equals."],
  ["boxed-types", "equatable-hashable"], ["equality", "strings"])

E("string-interpolation", "strings", "String interpolation → formatted() / concatenation",
  "\"Hello \\(name)\"", "\"Hello %s\".formatted(name)",
  "Java has no stable string interpolation (the string templates preview was withdrawn). Use concatenation, String.format or .formatted().",
  "low", [r"\\\("],
  "let msg = \"Hello \\(name), you are \\(age) years old\"",
  "String msg = \"Hello \" + name + \", you are \" + age + \" years old\";\nString msg2 = \"Hello %s, you are %d years old\".formatted(name, age);",
  ["Specifiers: %s string, %d integer, %.2f 2 decimals, %n newline, %x hex, %,d grouping."],
  ["multiline-strings"], ["strings", "formatting"])

E("multiline-strings", "strings", "Multi-line string → text block",
  "\"\"\" … \"\"\"", "\"\"\" … \"\"\" (text block)",
  "Text blocks work like Swift multi-line strings; the closing delimiter position sets stripped indentation.",
  "low", [r"\"\"\""],
  "let json = \"\"\"\n    { \"name\": \"\\(name)\" }\n    \"\"\"",
  "String json = \"\"\"\n        { \"name\": \"%s\" }\n        \"\"\".formatted(name);",
  ["No interpolation inside text blocks; combine with .formatted()."],
  ["string-interpolation"], ["strings"])

E("string-building", "strings", "Repeated += / joined → StringBuilder / String.join",
  "items.joined(separator: \", \")", "String.join(\", \", items)",
  "Strings are immutable. Use String.join or Collectors.joining; use StringBuilder for loops of appends.",
  "low", [r"\.joined\s*\("],
  "let result = items.joined(separator: \", \")",
  "String joined = String.join(\", \", items);\n\nvar sb = new StringBuilder();\nfor (String item : items) sb.append(item).append(\", \");\nString result = sb.toString();",
  [], ["stream-collectors"], ["strings", "performance"])

E("string-length", "strings", "count / String.Index → length() / charAt (UTF-16)",
  "s.count, s[s.startIndex]", "s.length(), s.charAt(0)",
  "Swift counts grapheme clusters; Java length() counts UTF-16 code units. Java allows direct integer indexing.",
  "medium", [r"String\.Index", r"\.(startIndex|endIndex|unicodeScalars|utf16)\b", r"\.index\s*\("],
  "let first = s[s.startIndex]   // String.Index, not Int\n\"👍\".count                   // 1",
  "\"👍\".length();               // 2 (surrogate pair)\n\"👍\".codePointCount(0, 2);   // 1\ns.charAt(0);                 // direct integer indexing",
  ["Iterate real characters with s.codePoints()."],
  ["character-utf16", "string-methods"], ["strings", "unicode"])

E("string-methods", "strings", "String method mapping",
  "uppercased(), hasPrefix, trimmingCharacters…", "toUpperCase(), startsWith, strip()…",
  "Most String methods have direct Java counterparts with different names.",
  "low", [r"\b(uppercased|lowercased|hasPrefix|hasSuffix|trimmingCharacters|replacingOccurrences)\s*\(", r"\.reversed\s*\(\s*\)",
          r"String\(repeating:"],
  "s.uppercased(); s.hasPrefix(\"a\"); s.trimmingCharacters(in: .whitespaces)",
  "s.toUpperCase(); s.startsWith(\"a\"); s.strip();",
  ["count → length(); isEmpty → isEmpty() (isBlank() for whitespace-only)",
   "lowercased() → toLowerCase(); hasSuffix → endsWith",
   "replacingOccurrences(of:with:) → replace(a, b) (replaceAll takes a regex)",
   "String(repeating: \"-\", count: 3) → \"-\".repeat(3)",
   "reversed() → new StringBuilder(s).reverse().toString()",
   "String(42) → String.valueOf(42)"],
  ["string-split-regex", "string-parse-number", "string-length"], ["strings"])

E("string-split-regex", "strings", "split / components(separatedBy:) → split (regex!)",
  "s.split(separator: \",\")", "s.split(\",\") — argument is a regex",
  "Java's String.split takes a regular expression and drops trailing empty strings by default.",
  "high", [r"\.split\s*\(", r"components\s*\(\s*separatedBy"],
  "let parts = version.components(separatedBy: \".\")",
  "String[] parts = version.split(\"\\\\.\");    // '.' must be escaped\nString[] all = csv.split(\",\", -1);       // -1 keeps trailing empties",
  ["split(\".\") splits on every character and returns an empty array.",
   "Pattern.quote(sep) escapes an arbitrary literal separator."],
  ["string-methods"], ["strings", "regex"])

E("string-parse-number", "strings", "Int(\"42\") → Integer.parseInt (throws)",
  "Int(\"42\") returns Int?", "Integer.parseInt(\"42\") throws NumberFormatException",
  "Parsing returns an optional in Swift but throws an unchecked NumberFormatException in Java.",
  "high", [r"\b(Int|Double|Float|Int64)\s*\(\s*(\"|[a-z]\w*\s*\))"],
  "let n = Int(text) ?? 0",
  "int n;\ntry {\n    n = Integer.parseInt(text);\n} catch (NumberFormatException e) {\n    n = 0;\n}",
  ["Long.parseLong, Double.parseDouble behave the same.",
   "Integer.parseInt(null) also throws NumberFormatException."],
  ["try-optional", "string-methods"], ["strings", "parsing", "exceptions"])

# ---------------------------------------------------------------- lambdas
E("closure-syntax", "lambdas", "Closure syntax → lambda syntax",
  "{ (a: Int, b: Int) -> Int in a + b }", "(a, b) -> a + b",
  "Lambdas use (params) -> body. Types are inferred from the target functional interface; block bodies need explicit return.",
  "low", [r"\{\s*\(?[\w\s,:<>\[\]?]*\)?\s*(->\s*[\w<>\[\]?]+\s*)?\bin\b"],
  "{ (a: Int, b: Int) -> Int in a + b }\n{ a, b in a + b }",
  "(int a, int b) -> a + b\n(a, b) -> a + b\nx -> x * 2\n() -> 42\n(a, b) -> {\n    int sum = a + b;\n    return sum * 2;\n}",
  ["The lambda always goes inside the parentheses: no trailing closures."],
  ["shorthand-args", "function-types", "trailing-closures"], ["lambdas", "syntax"])

E("shorthand-args", "lambdas", "$0, $1 → named parameters",
  "{ $0 + $1 }", "(a, b) -> a + b",
  "There is no $0 shorthand; every lambda parameter must be named. Unused parameters can be _ in Java 22+.",
  "low", [r"\$\d"],
  "items.map { $0 * 2 }",
  "items.stream().map(x -> x * 2).toList();\nmap.forEach((_, value) -> System.out.println(value));   // Java 22+",
  ["For `{ $0.name }`, prefer a method reference: Person::name."],
  ["closure-syntax", "method-references"], ["lambdas", "syntax"])

E("closure-capture-mutation", "lambdas", "Mutating captured variables → effectively final only",
  "var counter = 0; items.forEach { _ in counter += 1 }", "AtomicInteger, or avoid mutation",
  "Java lambdas can only capture local variables that are final or effectively final. Fields can still be mutated.",
  "high", [r"\{[^{}]*\bin\b[^{}]*\b\w+\s*([+\-*/]=|=\s)", r"\{[^{}]*\$\d[^{}]*\b\w+\s*[+\-*/]="],
  "var counter = 0\nitems.forEach { _ in counter += 1 }",
  "int counter = 0;\nitems.forEach(i -> counter++);        // compile error\n\nvar counter = new AtomicInteger();\nitems.forEach(i -> counter.incrementAndGet());\nlong count = items.stream().count();  // better: no mutation",
  ["this.field++ inside a lambda is allowed; only locals are restricted."],
  ["closure-syntax", "stream-basics"], ["lambdas", "closures", "capture"])

E("weak-self-capture", "lambdas", "[weak self] capture lists → not needed",
  "{ [weak self] in self?.reload() }", "() -> reload()",
  "this in a lambda is the enclosing instance. Cycles don't leak under GC, so capture lists have no equivalent.",
  "low", [r"\[\s*(weak|unowned)\s+self\s*\]", r"\[\s*(weak|unowned)\s+\w+"],
  "api.load { [weak self] data in self?.show(data) }",
  "api.load(data -> show(data));",
  [], ["arc-vs-gc", "lambda-vs-anonymous-class"], ["lambdas", "memory"])

E("trailing-closures", "lambdas", "@escaping / trailing closures → lambda inside parentheses",
  "animate(withDuration: 0.3) { view.alpha = 0 }", "animate(0.3, () -> view.setAlpha(0));",
  "Every Java lambda may escape, and there's no trailing-closure syntax.",
  "low", [r"@escaping", r"^(?![ \t]*(\}|func|init|if|guard|while|for|switch|else|catch|do|class|struct|enum|extension|protocol|actor|private|public|internal|fileprivate|open|static|override|mutating|convenience|required|final|@)\b)[^\n]*\w\)[ \t]*\{[^{}\n]*\}", r"^(?![ \t]*(\}|func|init|if|guard|while|for|switch|else|catch|do|class|struct|enum|extension|protocol|actor|private|public|internal|fileprivate|open|static|override|mutating|convenience|required|final|@)\b)[^\n]*(\w\)|\.\w+)[ \t]*\{[ \t]*(\[[^\]\n]*\][ \t]*)?(\w+([ \t]*,[ \t]*\w+)*[ \t]+in)?[ \t]*$"],
  "UIView.animate(withDuration: 0.3) { view.alpha = 0 }",
  "animate(0.3, () -> view.setAlpha(0));",
  [], ["closure-syntax"], ["lambdas", "syntax"])

E("function-types", "lambdas", "Function types → functional interfaces",
  "(Int) -> Int", "Function<Integer, Integer>",
  "Java has no function types. A lambda implements a functional interface and you call its method (apply, accept, test, get, run).",
  "medium", [r":\s*(@escaping\s+)?\(?\([^()]*\)\s*(throws\s+)?->"],
  "let square: (Int) -> Int = { $0 * $0 }\nsquare(4)",
  "Function<Integer, Integer> square = x -> x * x;\nsquare.apply(4);    // square(4) won't compile",
  ["() -> Void → Runnable.run()", "() -> T → Supplier<T>.get()", "(T) -> Void → Consumer<T>.accept(t)",
   "(T, U) -> Void → BiConsumer<T, U>.accept(t, u)", "(T) -> R → Function<T, R>.apply(t)",
   "(T, U) -> R → BiFunction<T, U, R>.apply(t, u)", "(T) -> Bool → Predicate<T>.test(t)",
   "(T) -> T → UnaryOperator<T>", "(T, T) -> T → BinaryOperator<T>",
   "(T, T) -> Bool (sort) → Comparator<T>.compare(a, b) returns int",
   "() throws -> T → Callable<T>.call()",
   "Primitive variants avoid boxing: IntFunction, ToIntFunction, IntPredicate, IntUnaryOperator…",
   "3+ parameters or checked exceptions → declare your own @FunctionalInterface."],
  ["closure-syntax", "optional-callback", "throwing-closures", "compose-lambdas"], ["lambdas", "functional-interfaces"])

E("optional-callback", "lambdas", "Optional closure property → Consumer field + null check",
  "var onComplete: ((Result) -> Void)?", "private Consumer<Result> onComplete;",
  "Store callbacks as functional-interface fields and null-check before calling.",
  "low", [r"\(\([^()]*\)\s*->\s*\w+\)\?"],
  "var onComplete: ((Result) -> Void)?\nonComplete?(result)",
  "private Consumer<Result> onComplete;\npublic void setOnComplete(Consumer<Result> handler) { this.onComplete = handler; }\nif (onComplete != null) onComplete.accept(result);",
  [], ["function-types"], ["lambdas", "callbacks"])

E("method-references", "lambdas", "Key paths / { $0.name } → method references",
  "people.map(\\.name)", "people.stream().map(Person::name)",
  "Method references are shorthand for lambdas that only call an existing method.",
  "low", [r"\(\s*\\\.\w+", r"\{\s*\$0\.\w+\s*\}"],
  "let names = people.map(\\.name)",
  "List<String> names = people.stream().map(Person::name).toList();",
  ["Static: Integer::parseInt", "Bound instance: System.out::println",
   "Instance of the parameter: String::toUpperCase", "Constructor: ArrayList::new"],
  ["shorthand-args", "stream-basics"], ["lambdas", "syntax"])

E("compose-lambdas", "lambdas", "Returning and composing functions",
  "func multiplier(_ f: Int) -> (Int) -> Int", "static Function<Integer, Integer> multiplier(int f)",
  "Return lambdas from methods and compose them with andThen / compose / and / negate.",
  "low", [r"->\s*\(\s*[\w<>\[\]?]*\s*\)\s*->"],
  "func multiplier(_ factor: Int) -> (Int) -> Int { { $0 * factor } }",
  "static Function<Integer, Integer> multiplier(int factor) {\n    return x -> x * factor;\n}\ntriple.andThen(plusOne).apply(5);   // (5 * 3) + 1 = 16\nnotEmpty.and(shortWord).test(\"hi\");",
  ["A lambda cannot be generic itself; use a generic method.",
   "A lambda can't easily call itself recursively; use a method."],
  ["function-types"], ["lambdas", "functional"])

E("lambda-vs-anonymous-class", "lambdas", "Anonymous classes (legacy code)",
  "(n/a)", "new Runnable() { public void run() { … } }",
  "Older Java code uses anonymous classes where you'd now write a lambda. Inside an anonymous class, this is the anonymous object.",
  "low", [],
  None,
  "Runnable r = new Runnable() {\n    @Override public void run() { System.out.println(\"old style\"); }\n};\nRunnable r2 = () -> System.out.println(\"lambda\");",
  [], ["closure-syntax"], ["lambdas", "legacy"])

# ---------------------------------------------------------------- control flow
E("if-statement", "control-flow", "if → if (parentheses required)",
  "if score > 90 { }", "if (score > 90) { }",
  "Conditions need parentheses and must be boolean. Braces are optional but strongly recommended.",
  "low", [r"^[ \t]*(\}[ \t]*else[ \t]+)?if[ \t]+(?!let\b|var\b|case\b)[^({\n]"],
  "if score > 90 { grade = \"A\" } else if score > 80 { grade = \"B\" }",
  "if (score > 90) {\n    grade = \"A\";\n} else if (score > 80) {\n    grade = \"B\";\n}",
  ["Ternary is identical: isOn ? \"On\" : \"Off\"."], ["optional-binding"], ["control-flow", "syntax"])

E("guard-statement", "control-flow", "guard … else → inverted if + early return",
  "guard count > 0 else { return }", "if (count <= 0) { return; }",
  "guard becomes an if with the inverted condition and an early exit.",
  "low", [r"\bguard\s+(?!let\b|var\b)"],
  "guard count > 0 else { return }",
  "if (count <= 0) {\n    return;\n}",
  [], ["optional-binding"], ["control-flow"])

E("type-cast-binding", "control-flow", "as? / is → instanceof pattern matching",
  "if let c = shape as? Circle { }", "if (shape instanceof Circle c) { }",
  "Type-check-and-bind uses pattern matching for instanceof.",
  "medium", [r"\bas\?", r"\bas!", r"\bis\s+[A-Z]\w*"],
  "if let c = shape as? Circle { print(c.radius) }",
  "if (shape instanceof Circle c) {\n    System.out.println(c.radius());\n}",
  ["as! → a plain cast (Circle) shape, which throws ClassCastException on failure."],
  ["switch-patterns"], ["control-flow", "casting", "pattern-matching"])

E("switch-arrow", "control-flow", "switch → arrow-form switch (no fallthrough)",
  "switch day { case .saturday, .sunday: … }", "switch (day) { case SATURDAY, SUNDAY -> … }",
  "Use the arrow form. The old colon form falls through unless you break.",
  "medium", [r"\bswitch\b"],
  "switch day {\ncase .saturday, .sunday: print(\"Weekend\")\ndefault: print(\"Weekday\")\n}",
  "switch (day) {\n    case SATURDAY, SUNDAY -> System.out.println(\"Weekend\");\n    default -> System.out.println(\"Weekday\");\n}",
  ["case X: (colon) silently falls into the next case without break.",
   "Switch over enums: write the bare constant name (SATURDAY), not Day.SATURDAY."],
  ["switch-expression", "switch-patterns"], ["control-flow", "switch"])

E("switch-expression", "control-flow", "let x = switch → switch expression with yield",
  "let type = switch day { … }", "String type = switch (day) { … };",
  "Switch can be an expression. Use yield to return a value from a block branch.",
  "low", [r"=\s*switch\b"],
  "let type = switch day {\ncase .saturday, .sunday: \"Weekend\"\ndefault: \"Weekday\"\n}",
  "String type = switch (day) {\n    case SATURDAY, SUNDAY -> \"Weekend\";\n    default -> {\n        log(\"weekday\");\n        yield \"Weekday\";\n    }\n};",
  [], ["switch-arrow"], ["control-flow", "switch"])

E("switch-patterns", "control-flow", "switch on associated values → record patterns + when",
  "case .circle(let r): … / case … where", "case Circle c -> … / case Rect r when …",
  "Pattern-matching switch over a sealed type is exhaustive; when is Swift's where; records can be deconstructed.",
  "medium", [r"case\s+\.?\w+\s*\(\s*(let|var)\b", r"case\s+(let|var)\s+\.", r"^[ \t]*case\b[^:\n]*\bwhere\b"],
  "switch shape {\ncase .circle(let r): return .pi * r * r\ncase .rect(let w, let h) where w == h: return w * w\ncase .rect(let w, let h): return w * h\n}",
  "double area = switch (shape) {\n    case Circle c -> Math.PI * c.radius() * c.radius();\n    case Rect r when r.w() == r.h() -> r.w() * r.w();\n    case Rect(double w, double h) -> w * h;\n};   // no default: Shape is sealed",
  [], ["enum-associated-values", "sealed-hierarchies"], ["control-flow", "pattern-matching", "sealed"], "Java 21")

E("range-loops", "control-flow", "for i in 0..<n → classic for / IntStream.range",
  "for i in 0..<n", "for (int i = 0; i < n; i++)",
  "Ranges become index loops, or IntStream.range (exclusive) / rangeClosed (inclusive).",
  "low", [r"\.\.<", r"\w\s*\.\.\.\s*\w"],
  "for i in 0..<n { }\nfor i in 0...n { }",
  "for (int i = 0; i < n; i++) { }\nfor (int i = 0; i <= n; i++) { }\nIntStream.range(0, n).forEach(i -> ...);",
  [], ["stride-loops", "enumerated-loops"], ["control-flow", "loops"])

E("stride-loops", "control-flow", "stride(from:to:by:) → for with step",
  "for i in stride(from: 10, to: 0, by: -2)", "for (int i = 10; i > 0; i -= 2)",
  "Strides become classic for loops with a custom step.",
  "low", [r"\bstride\s*\("],
  "for i in stride(from: 10, to: 0, by: -2) { }",
  "for (int i = 10; i > 0; i -= 2) { }",
  [], ["range-loops"], ["control-flow", "loops"])

E("enumerated-loops", "control-flow", "enumerated() → index loop",
  "for (i, item) in items.enumerated()", "for (int i = 0; i < items.size(); i++)",
  "There's no enumerated(); loop over indices.",
  "low", [r"\.enumerated\s*\(\s*\)"],
  "for (i, item) in items.enumerated() { }",
  "for (int i = 0; i < items.size(); i++) {\n    var item = items.get(i);\n}",
  [], ["range-loops"], ["control-flow", "loops"])

E("dictionary-loops", "control-flow", "for (k, v) in dict → entrySet()",
  "for (key, value) in dict", "for (var e : map.entrySet())",
  "Iterate a Map's entries, or use map.forEach((k, v) -> …).",
  "low", [r"for\s*\(\s*\w+\s*,\s*\w+\s*\)\s*in\s+(?!.*enumerated)"],
  "for (name, age) in ages { print(name, age) }",
  "for (var e : ages.entrySet()) {\n    System.out.println(e.getKey() + \" \" + e.getValue());\n}\nages.forEach((name, age) -> ...);",
  ["HashMap iteration order is unspecified (like Swift Dictionary). LinkedHashMap keeps insertion order."],
  ["collection-types"], ["control-flow", "loops", "maps"])

E("repeat-while", "control-flow", "repeat { } while → do { } while ();",
  "repeat { } while cond", "do { } while (cond);",
  "repeat-while is do-while, with a trailing semicolon.",
  "low", [r"\brepeat\s*\{"],
  "repeat { attempt += 1 } while attempt < 3",
  "do { attempt++; } while (attempt < 3);",
  [], [], ["control-flow", "loops"])

E("defer", "control-flow", "defer → finally / try-with-resources",
  "defer { file.close() }", "try { … } finally { file.close(); }",
  "defer becomes a finally block; for resources prefer try-with-resources.",
  "medium", [r"\bdefer\s*\{"],
  "defer { file.close() }",
  "try {\n    // work\n} finally {\n    file.close();\n}\n\ntry (var reader = Files.newBufferedReader(path)) {\n    // use reader\n}",
  [], ["try-with-resources", "deinit-autocloseable"], ["control-flow", "resources"])

# ---------------------------------------------------------------- objects
E("class-declaration", "objects", "class → class (one public class per file)",
  "class BankAccount { init(…) }", "public class BankAccount { BankAccount(…) }",
  "Constructors are named after the class, new is required, and a public top-level class must live in a file of the same name.",
  "medium", [r"^[ \t]*(\w+[ \t]+)*class[ \t]+[A-Z]\w*"],
  "class BankAccount {\n    let owner: String\n    private(set) var balance = 0.0\n    init(owner: String) { self.owner = owner }\n    func deposit(_ amount: Double) { balance += amount }\n}",
  "public class BankAccount {\n    private final String owner;\n    private double balance;\n\n    public BankAccount(String owner) { this.owner = owner; }\n    public void deposit(double amount) { balance += amount; }\n    public double getBalance() { return balance; }\n}\nBankAccount acct = new BankAccount(\"Ana\");",
  ["Avoid calling overridable methods from constructors: subclass fields aren't set yet (no two-phase init).",
   "Fields default to 0/false/null; Swift would have forced initialization."],
  ["properties", "open-by-default", "init-chaining", "field-defaults"], ["classes"])

E("properties", "objects", "Properties → private fields + getters/setters",
  "var name: String / var area: Double { w * h } / didSet", "private String name; getName()/setName(); getArea()",
  "Java has no properties. Use private fields with getters/setters; computed properties become methods; didSet logic goes in the setter.",
  "low", [r"\b(didSet|willSet)\b", r"\bvar\s+\w+\s*:\s*[\w<>\[\]?]+\s*\{", r"private\s*\(\s*set\s*\)"],
  "var area: Double { w * h }\nprivate(set) var count = 0\nvar name: String { didSet { save() } }",
  "public double getArea() { return w * h; }\n\nprivate int count;\npublic int getCount() { return count; }\n\npublic void setName(String name) {\n    this.name = name;\n    save();\n}",
  ["Records use accessors without get: point.x()."],
  ["class-declaration", "struct-to-record"], ["classes", "properties"])

E("deinit-autocloseable", "objects", "deinit → AutoCloseable + try-with-resources",
  "deinit { close() }", "implements AutoCloseable + try (var x = …) { }",
  "There is no deinit and GC timing is unspecified. finalize() is deprecated. Implement AutoCloseable for deterministic cleanup.",
  "high", [r"\bdeinit\b"],
  "deinit { connection.close() }",
  "public class Connection implements AutoCloseable {\n    @Override public void close() { /* release */ }\n}\ntry (var conn = new Connection()) {\n    // use conn\n}   // close() runs here",
  ["Never rely on GC to release files, sockets or locks."],
  ["arc-vs-gc", "try-with-resources", "defer"], ["memory", "resources", "lifecycle"])

E("static-members", "objects", "static let/func → static final / static; no class func",
  "static let maxUsers = 100 / class func", "public static final int MAX_USERS = 100;",
  "Constants are static final in UPPER_SNAKE_CASE. Statics are never polymorphic: there's no class func equivalent.",
  "low", [r"\bstatic\s+(let|var|func)\b", r"\bclass\s+(func|var)\b"],
  "static let maxUsers = 100\nstatic func create() -> Config",
  "public static final int MAX_USERS = 100;\npublic static Config create() { ... }\nConfig.create();",
  ["class func (overridable static) → instance method or a strategy object."],
  ["free-functions"], ["classes", "static"])

E("concurrency-primitives", "objects", "actors / locks / queues → volatile, synchronized, atomics",
  "actor, NSLock, DispatchQueue, @MainActor", "volatile, synchronized, AtomicInteger, java.util.concurrent",
  "volatile gives visibility (good for flags), not atomicity. Use Atomic* types or synchronized for compound operations.",
  "high", [r"\bactor\s+\w+", r"\bNSLock\b", r"\bDispatchQueue\b", r"@MainActor", r"\bSendable\b", r"\basync\b", r"\bawait\b"],
  "actor Counter { var value = 0; func increment() { value += 1 } }",
  "private volatile boolean running = true;           // visibility only\nprivate final AtomicInteger count = new AtomicInteger();\ncount.incrementAndGet();                           // atomic\npublic synchronized void transfer(...) { ... }      // critical section",
  ["count++ on a volatile field is still a race.",
   "async/await has no direct Java syntax; use CompletableFuture or (Java 21) virtual threads with plain blocking code."],
  [], ["concurrency", "threads"])

E("field-defaults", "objects", "Fields get default values (null!)",
  "Stored properties must be initialized", "Fields default to 0, 0.0, false, '\\u0000', null",
  "Java fields are silently default-initialized; local variables are not and must be assigned before use.",
  "medium", [],
  "class Example { var name: String }   // compile error without init",
  "class Example {\n    int count;      // 0\n    String name;    // null\n}",
  ["Make fields final to force initialization in every constructor."],
  ["class-declaration", "optional-type"], ["classes", "null-safety"])

E("init-chaining", "objects", "convenience init → this(…)",
  "convenience init(name:) { self.init(name: name, age: 0) }", "Person(String name) { this(name, 0); }",
  "Constructor chaining uses this(…) or super(…), which must be the first statement.",
  "low", [r"\bconvenience\s+init\b", r"\bself\.init\s*\("],
  "init(name: String, age: Int) { … }\nconvenience init(name: String) { self.init(name: name, age: 0) }",
  "Person(String name, int age) { this.name = name; this.age = age; }\nPerson(String name) { this(name, 0); }",
  ["Initialization order: static initializers (once) → super(...) → field initializers/instance blocks in source order → rest of constructor."],
  ["default-parameters", "class-declaration"], ["classes", "constructors"])

E("default-parameters", "objects", "Default parameter values → overloads or builder",
  "init(host: String, port: Int = 80)", "overloaded constructors / builder",
  "Java has no default parameter values. Use overloads that delegate, or a builder / parameter record for many options.",
  "medium", [r"\b(func\s+\w+|init)\s*(<[^>]*>)?\s*\([^)]*:\s*[^,)=]+=\s*[^=]"],
  "init(host: String, port: Int = 80, secure: Bool = false)",
  "Server(String host) { this(host, 80, false); }\nServer(String host, int port) { this(host, port, false); }\nServer(String host, int port, boolean secure) { ... }\n\nServer s = Server.builder().host(\"x\").port(8080).secure(true).build();",
  [], ["init-chaining", "argument-labels"], ["functions", "constructors", "api-design"])

E("failable-init", "objects", "init? → static factory returning Optional",
  "init?(raw: String)", "static Optional<Email> parse(String raw)",
  "Constructors can't return null. Use a static factory returning Optional, or throw IllegalArgumentException.",
  "medium", [r"\binit\s*\?"],
  "init?(raw: String) { guard raw.contains(\"@\") else { return nil } … }",
  "public static Optional<Email> parse(String raw) {\n    return raw.contains(\"@\") ? Optional.of(new Email(raw)) : Optional.empty();\n}",
  [], ["optional-return"], ["constructors", "optionals"])

E("lazy-var", "objects", "lazy var → manual lazy initialization",
  "lazy var thing = ExpensiveThing()", "null-check in a getter",
  "Implement laziness in the getter. The simple version isn't thread-safe; for a lazy static singleton use the holder-class idiom.",
  "low", [r"\blazy\s+var\b"],
  "lazy var thing = ExpensiveThing()",
  "private ExpensiveThing thing;\nExpensiveThing getThing() {\n    if (thing == null) thing = new ExpensiveThing();\n    return thing;\n}",
  [], ["properties"], ["classes", "initialization"])

# ---------------------------------------------------------------- oop
E("access-modifiers", "oop", "Access control → public / protected / package-private / private",
  "open, public, internal, fileprivate, private", "public, public final, (package-private), private, protected",
  "Swift internal ≈ Java package-private (no keyword). fileprivate has no equivalent. Java adds protected (package + subclasses).",
  "medium", [r"\b(open|fileprivate|internal)\s+(class|func|var|let|struct|enum|protocol|init)\b"],
  "open class Base { }\ninternal func helper() { }\nfileprivate var cache = [String: Int]()",
  "public class Base { }          // open by default\nvoid helper() { }              // package-private\nprivate Map<String, Integer> cache = new HashMap<>();",
  ["Swift public (not open) → public + final."],
  ["open-by-default"], ["access-control"])

E("variable-shadowing", "oop", "Shadowing locals → compile error in Java",
  "if let x = x / nested let x", "reuse the variable or pick a new name",
  "Java forbids redeclaring a local variable in a nested block (a local may still shadow a field).",
  "medium", [r"\b(if|guard)\s+let\s+(\w+)\s*=\s*\2\b", r"\b(if|guard)\s+let\s+\w+\s*(\{|else\b|,)"],
  "if let user = user { … }",
  "if (user != null) { … }      // just use user\nint x = 1; if (true) { int x = 2; }   // compile error",
  [], ["optional-binding"], ["scope"])

E("inheritance", "oop", "class Dog: Animal → extends + @Override",
  "class Dog: Animal { override func speak() }", "class Dog extends Animal { @Override public String speak() }",
  "Use extends, call the parent constructor with super(...), and always annotate overrides with @Override.",
  "low", [r"\boverride\s+(func|var|init)\b", r"\bsuper\.init\s*\("],
  "class Dog: Animal {\n    override func speak() -> String { \"Woof \" + super.speak() }\n}",
  "public class Dog extends Animal {\n    public Dog(String name) { super(name); }\n    @Override\n    public String speak() { return \"Woof \" + super.speak(); }\n}",
  ["Every class extends Object (equals, hashCode, toString)."],
  ["equatable-hashable", "abstract-classes"], ["inheritance"])

E("equatable-hashable", "oop", "Equatable / Hashable → equals() + hashCode()",
  "struct User: Hashable", "override equals and hashCode (or use a record)",
  "Map keys, sets, contains and indexOf use equals/hashCode. Records generate both; for classes implement them together.",
  "high", [r":[^{\n]*\b(Equatable|Hashable|Comparable)\b"],
  "struct User: Hashable { let id: String }",
  "record User(String id) {}   // equals + hashCode generated\n\n@Override public boolean equals(Object o) {\n    return o instanceof User u && id.equals(u.id);\n}\n@Override public int hashCode() { return Objects.hash(id); }",
  ["Overriding equals without hashCode silently breaks HashMap/HashSet.",
   "Comparable → implements Comparable<T> with compareTo returning int."],
  ["equality-operator", "struct-to-record", "collection-types"], ["equality", "hashing"])

E("protocols", "oop", "protocol → interface (default methods)",
  "protocol Drawable { func draw() } + extension", "interface Drawable { void draw(); default … }",
  "Protocols become interfaces; protocol-extension implementations become default methods. A class can implement many interfaces.",
  "low", [r"\bprotocol\s+\w+"],
  "protocol Drawable { func draw() }\nextension Drawable { func describe() -> String { \"drawable\" } }",
  "public interface Drawable {\n    void draw();\n    default String describe() { return \"drawable\"; }\n}\npublic class Box implements Drawable {\n    @Override public void draw() { }\n}",
  ["No retroactive conformance: you can't make an existing class implement your interface."],
  ["extensions", "associated-types", "abstract-classes"], ["interfaces"])

E("extensions", "oop", "extension → static utility class (no extension methods)",
  "extension String { func isPalindrome() -> Bool }", "StringUtils.isPalindrome(s)",
  "You can't add methods to existing classes. Use a final utility class with a private constructor, or default methods on your own interfaces.",
  "medium", [r"^[ \t]*(\w+[ \t]+)*extension[ \t]+\w+"],
  "extension String {\n    var isPalindrome: Bool { self == String(reversed()) }\n}",
  "public final class StringUtils {\n    private StringUtils() {}\n    public static boolean isPalindrome(String s) { ... }\n}\nStringUtils.isPalindrome(\"level\");",
  ["Extensions used for protocol conformance → put implements on the class itself."],
  ["protocols", "free-functions"], ["extensions"])

E("associated-types", "oop", "associatedtype → interface type parameter",
  "protocol Container { associatedtype Item }", "interface Container<T> { T get(); }",
  "Associated types become generic type parameters on the interface.",
  "low", [r"\bassociatedtype\b"],
  "protocol Container { associatedtype Item; func get() -> Item }",
  "interface Container<T> { T get(); }",
  [], ["protocols", "generic-methods"], ["generics", "interfaces"])

E("abstract-classes", "oop", "fatalError() stubs → abstract class",
  "func area() -> Double { fatalError(\"subclass must override\") }", "public abstract double area();",
  "Java has abstract classes. Use them for shared state/constructor logic; use interfaces for pure contracts.",
  "low", [r"fatalError\s*\("],
  "class Shape { func area() -> Double { fatalError(\"override\") } }",
  "public abstract class Shape {\n    public abstract double area();\n    public String describe() { return \"area \" + area(); }\n}",
  ["fatalError elsewhere → throw new IllegalStateException(...) or UnsupportedOperationException."],
  ["protocols", "inheritance"], ["inheritance", "abstraction"])

E("sealed-hierarchies", "oop", "Closed set of types → sealed interface",
  "enum Result { case success(String), failure(String) }", "sealed interface Result permits Success, Failure {}",
  "sealed restricts implementors, which enables exhaustive switch.",
  "low", [r"\bResult\s*<"],
  "let r: Result<String, Error>",
  "public sealed interface Result permits Success, Failure {}\npublic record Success(String data) implements Result {}\npublic record Failure(String error) implements Result {}",
  ["Swift's Result<T, E> is often just a return value + exception in Java."],
  ["enum-associated-values", "switch-patterns"], ["sealed", "records"], "Java 17")

E("type-erasure", "oop", "Generics are erased at runtime",
  "T.self, T(), x is [String]", "pass Class<T> or Supplier<T>",
  "Java generics are erased: new T(), T.class and instanceof List<String> aren't possible.",
  "medium", [r"\b[A-Z]\.self\b", r"\b[A-Z]\.Type\b", r"\bis\s+\[\w+\]"],
  "func make<T: Decodable>(_ type: T.Type) -> T",
  "<T> T make(Class<T> type) { ... }\n<T> T make(Supplier<T> factory) { return factory.get(); }",
  [], ["generic-methods"], ["generics"])

# ---------------------------------------------------------------- exceptions
E("throws-checked-unchecked", "exceptions", "throws → checked or unchecked (decide!)",
  "func validate() throws", "void validate() throws ValidationException / RuntimeException",
  "Checked exceptions (extend Exception) must be declared or caught; unchecked (extend RuntimeException) need not be. Choose deliberately.",
  "high", [r"\bthrows\b", r"\bthrow\s+\w"],
  "func validate(_ s: String) throws {\n    if s.count < 3 { throw ValidationError.tooShort }\n}",
  "public void validate(String s) throws ValidationException {\n    if (s.length() < 3) {\n        throw new ValidationException(\"Too short: \" + s);\n    }\n}",
  ["Checked: recoverable conditions (I/O, parsing input). Unchecked: programming errors.",
   "Never catch Error (OutOfMemoryError etc.).",
   "Built-ins: IllegalArgumentException, IllegalStateException, UnsupportedOperationException, IndexOutOfBoundsException."],
  ["error-types", "do-catch", "throwing-closures"], ["exceptions"])

E("error-types", "exceptions", "enum …: Error → exception class",
  "enum ValidationError: Error { case tooShort }", "class ValidationException extends Exception",
  "Errors are classes extending Exception or RuntimeException; enum cases become subclasses or a message/field.",
  "medium", [r"\b(enum|struct|class)[ \t]+\w+[ \t]*:[^{\n]*\bError\b"],
  "enum ValidationError: Error { case tooShort }",
  "public class ValidationException extends Exception {\n    public ValidationException(String message) { super(message); }\n}",
  ["Wrap with a cause to keep the chain: throw new RepositoryException(\"msg\", e);"],
  ["throws-checked-unchecked"], ["exceptions"])

E("do-catch", "exceptions", "do { try } catch → try { } catch (Type e)",
  "do { try f() } catch { }", "try { f(); } catch (SomeException e) { }",
  "No try keyword per call. Catch the most specific types first; multi-catch with |; finally always runs.",
  "low", [r"\bdo\s*\{", r"\bcatch\b"],
  "do {\n    try validate(input)\n} catch ValidationError.tooShort {\n    print(\"short\")\n} catch {\n    print(error)\n}",
  "try {\n    validate(input);\n} catch (ValidationException e) {\n    System.out.println(e.getMessage());\n} catch (IOException | ParseException e) {\n    log(e);\n} finally {\n    cleanup();\n}",
  ["Catching Exception broadly is usually a smell."],
  ["throws-checked-unchecked", "try-optional"], ["exceptions"])

E("try-optional", "exceptions", "try? → catch and return Optional.empty()",
  "let x = try? f()", "try { … } catch (E e) { Optional.empty() }",
  "There's no try?; catch the exception and fall back to null or Optional.empty().",
  "medium", [r"\btry\?"],
  "let parsed = try? parse(text)",
  "Optional<Integer> parsed;\ntry {\n    parsed = Optional.of(Integer.parseInt(text));\n} catch (NumberFormatException e) {\n    parsed = Optional.empty();\n}",
  [], ["try-force", "string-parse-number"], ["exceptions", "optionals"])

E("try-force", "exceptions", "try! → wrap as unchecked exception",
  "let s = try! load()", "catch (IOException e) { throw new UncheckedIOException(e); }",
  "try! becomes catching the checked exception and rethrowing it unchecked.",
  "medium", [r"\btry!"],
  "let text = try! String(contentsOf: url)",
  "try {\n    return Files.readString(path);\n} catch (IOException e) {\n    throw new UncheckedIOException(e);\n}",
  [], ["try-optional"], ["exceptions"])

E("try-with-resources", "exceptions", "Resource cleanup → try-with-resources",
  "defer { reader.close() }", "try (var reader = …) { }",
  "Resources declared in try ( … ) are closed automatically in reverse order, even on exceptions.",
  "medium", [r"\.close\s*\(\s*\)"],
  "let reader = try FileHandle(forReadingFrom: url)\ndefer { try? reader.close() }",
  "try (var reader = Files.newBufferedReader(path);\n     var writer = Files.newBufferedWriter(out)) {\n    writer.write(reader.readLine());\n}",
  [], ["defer", "deinit-autocloseable"], ["exceptions", "resources"])

E("throwing-closures", "exceptions", "Throwing closures → standard interfaces can't throw checked exceptions",
  "(T) throws -> R / rethrows", "wrap inside the lambda, or a custom @FunctionalInterface",
  "Function, Consumer etc. can't throw checked exceptions. Catch and wrap inside the lambda, or declare your own interface.",
  "high", [r"\)\s*throws\s*->", r"\brethrows\b", r"\{[^{}\n]*\btry\b(?![?!])"],
  "try paths.forEach { try process($0) }",
  "paths.forEach(p -> {\n    try {\n        process(p);\n    } catch (IOException e) {\n        throw new UncheckedIOException(e);\n    }\n});\n\n@FunctionalInterface\ninterface IOAction { void run() throws IOException; }",
  [], ["function-types", "throws-checked-unchecked"], ["exceptions", "lambdas"])

# ---------------------------------------------------------------- collections
E("collection-types", "collections", "Array / Dictionary / Set → List / Map / Set (references!)",
  "[T], [K: V], Set<T>", "List<T> / Map<K,V> / Set<T> (ArrayList, HashMap, HashSet)",
  "Swift collections are value types that copy on assignment. Java collections are references: assigning shares the same object.",
  "high", [r"\[\s*[A-Z]\w*\s*\]", r"\[\s*[A-Z]\w*\s*:\s*[A-Z]\w*\s*\]", r"\b(Array|Dictionary|Set)\s*<", r"^[ \t]*(let|var)[ \t]+\w+[ \t]*=[ \t]*\["],
  "var a = [\"x\"]\nvar b = a\nb.append(\"y\")   // a is still [\"x\"]",
  "List<String> a = new ArrayList<>(List.of(\"x\"));\nList<String> b = a;\nb.add(\"y\");                                // a also has \"y\"!\nList<String> copy = new ArrayList<>(a);   // explicit copy",
  ["Declare with the interface type: List<String> names = new ArrayList<>();",
   "Map ordering: HashMap (none), LinkedHashMap (insertion), TreeMap (sorted).",
   "Deque/stack/queue → ArrayDeque.",
   "Generics take reference types only: List<Integer>, never List<int>."],
  ["immutable-collections", "array-operations", "dictionary-operations", "boxed-types"], ["collections", "value-semantics"])

E("arrays", "collections", "Fixed-size arrays (rare)",
  "Array(repeating: 0, count: 5)", "new int[5]",
  "Java arrays are fixed-size; .length is a field. Prefer List in most code.",
  "low", [r"Array\s*\(\s*repeating:"],
  "var nums = Array(repeating: 0, count: 5)",
  "int[] nums = new int[5];           // [0, 0, 0, 0, 0]\nint[] primes = {2, 3, 5, 7};\nnums.length;                       // field, not a method\nArrays.toString(primes);\nArrays.equals(a, b);               // a.equals(b) compares references!",
  ["String[] names = new String[3] is [null, null, null]."],
  ["collection-types"], ["collections", "arrays"])

E("immutable-collections", "collections", "let array → List.of (fails at runtime)",
  "let fixed = [\"a\", \"b\"]", "List.of(\"a\", \"b\")",
  "List.of / Map.of / Set.of create unmodifiable collections, but modification fails at runtime (UnsupportedOperationException), not compile time.",
  "medium", [r"\blet\s+\w+\s*(:\s*\[[^\]]+\])?\s*=\s*\["],
  "let fixed = [\"a\", \"b\"]",
  "List<String> fixed = List.of(\"a\", \"b\");\nfixed.add(\"c\");   // UnsupportedOperationException at runtime\nList<String> mutable = new ArrayList<>(List.of(\"a\", \"b\"));",
  ["List.of/Map.of/Set.of reject null elements.",
   "stream.toList() also returns an unmodifiable list."],
  ["collection-types"], ["collections", "immutability"])

E("array-operations", "collections", "Array methods → List methods",
  "append, insert(at:), remove(at:), first, firstIndex(of:)", "add, add(i, x), remove(i), getFirst(), indexOf",
  "Most array operations map directly, with a few traps: getFirst throws on empty, indexOf returns -1.",
  "medium", [r"\.(append|insert|firstIndex|lastIndex)\s*\(", r"\.remove\s*\(\s*at:", r"\.(first|last)\b(?!\s*\()"],
  "arr.append(x); arr.insert(x, at: 0); let i = arr.firstIndex(of: x); let f = arr.first",
  "list.add(x); list.add(0, x); int i = list.indexOf(x); var f = list.getFirst();",
  ["count → size(); arr[0] → get(0); arr[0] = x → set(0, x)",
   "first/last → getFirst()/getLast() (Java 21) THROW if empty instead of returning nil",
   "firstIndex(of:) → indexOf returns -1, not nil",
   "List<Integer>.remove(Integer) removes by value; remove(int) by index",
   "sort() → list.sort(Comparator.naturalOrder()); reversed() → list.reversed() (a view, Java 21)",
   "removeAll(where:) → removeIf(...); removing inside for-each throws ConcurrentModificationException"],
  ["collection-types", "dictionary-operations"], ["collections", "lists"], "Java 21")

E("dictionary-operations", "collections", "Dictionary subscripts → Map methods",
  "dict[key], dict[key, default: 0] += 1, dict[key] = nil", "map.get (null), merge, remove",
  "map.get returns null when missing. Use getOrDefault, merge and remove for the common Swift subscript idioms.",
  "medium", [r"\[\s*[^\]]+,\s*default:", r"\w\[[^\]]+\]\s*=\s*nil\b"],
  "counts[word, default: 0] += 1\ndict[key] = nil",
  "counts.merge(word, 1, Integer::sum);\nint n = counts.getOrDefault(word, 0);\nmap.remove(key);",
  ["dict.keys / values → map.keySet() / map.values()", "dict[key] = v → map.put(key, v)"],
  ["collection-types", "dictionary-loops"], ["collections", "maps"])

E("set-operations", "collections", "union / intersection → addAll / retainAll (mutating)",
  "a.union(b), a.intersection(b)", "copy then addAll / retainAll",
  "Java's set algebra methods mutate the receiver, so copy first.",
  "medium", [r"\.(union|intersection|subtracting|symmetricDifference|formUnion)\s*\("],
  "let u = a.union(b)",
  "var u = new HashSet<>(a); u.addAll(b);\nvar i = new HashSet<>(a); i.retainAll(b);\nvar d = new HashSet<>(a); d.removeAll(b);",
  [], ["collection-types"], ["collections", "sets"])

# ---------------------------------------------------------------- streams
E("stream-basics", "streams", "map/filter chains → stream() … toList()",
  "people.filter { … }.map { … }.sorted()", "people.stream().filter(…).map(…).sorted().toList()",
  "Streams are explicit: enter with .stream(), exit with a terminal operation. They're lazy, single-use, and don't modify the source.",
  "low", [r"\.(map|filter|flatMap|forEach)\s*[\({]"],
  "let result = people\n    .filter { $0.age >= 18 }\n    .map { $0.name }\n    .sorted()",
  "List<String> result = people.stream()\n        .filter(p -> p.age() >= 18)\n        .map(Person::name)\n        .sorted()\n        .toList();",
  ["Don't mutate outside state from map/filter.",
   "A plain loop is often clearer for complex logic with early exits.",
   "parallelStream() is rarely a win; measure first."],
  ["compact-map", "stream-reduce", "stream-sorting", "stream-search", "stream-collectors"], ["streams"])

E("compact-map", "streams", "compactMap → filter(nonNull) / Optional::stream",
  ".compactMap { Int($0) }", ".map(...).filter(Objects::nonNull)",
  "compactMap becomes map + filter(Objects::nonNull), or flatMap over Optional results.",
  "low", [r"\.compactMap\b"],
  "let ids = strings.compactMap { Int($0) }",
  "List<User> users = ids.stream()\n        .map(repo::findOrNull)\n        .filter(Objects::nonNull)\n        .toList();\n// Optional-returning: .flatMap(id -> repo.find(id).stream())",
  [], ["stream-basics"], ["streams", "optionals"])

E("stream-reduce", "streams", "reduce → reduce / mapToInt().sum()",
  ".reduce(0, +)", ".mapToInt(...).sum() / .reduce(0, Integer::sum)",
  "Use primitive streams (mapToInt/mapToDouble) for sums and averages; they avoid boxing.",
  "low", [r"\.reduce\s*\("],
  "let total = orders.reduce(0) { $0 + $1.quantity }",
  "int total = orders.stream().mapToInt(Order::quantity).sum();\ndouble avg = scores.stream().mapToDouble(Double::doubleValue).average().orElse(0);",
  ["count() returns long."], ["stream-basics"], ["streams"])

E("stream-sorting", "streams", "sorted { } / sorted(by:) → Comparator",
  "people.sorted { $0.age < $1.age }", "sorted(Comparator.comparing(Person::age))",
  "Build comparators with Comparator.comparing and thenComparing instead of a less-than closure.",
  "low", [r"\.(sorted|sort)\s*(\{|\(\s*by:)", r"\.(min|max)\s*(\{|\(\s*by:)"],
  "let sorted = people.sorted { $0.age < $1.age }\nlet desc = nums.sorted(by: >)",
  "people.sort(Comparator.comparing(Person::lastName)\n        .thenComparing(Person::firstName)\n        .thenComparing(Person::age, Comparator.reverseOrder()));\nnums.stream().sorted(Comparator.reverseOrder()).toList();",
  ["min()/max() take a comparator and return Optional."], ["stream-basics"], ["streams", "sorting"])

E("stream-search", "streams", "first(where:) / contains(where:) / allSatisfy → findFirst / anyMatch / allMatch",
  "items.first(where: { … })", "items.stream().filter(…).findFirst()",
  "Searching predicates map to findFirst (returns Optional), anyMatch, allMatch, noneMatch.",
  "low", [r"\.first\s*\(\s*where:", r"\.contains\s*\(\s*where:", r"\.allSatisfy\b", r"\.(prefix|dropFirst|dropLast)\s*\("],
  "let admin = users.first(where: { $0.isAdmin })",
  "Optional<User> admin = users.stream().filter(User::isAdmin).findFirst();\nboolean any = users.stream().anyMatch(User::isAdmin);",
  ["prefix(n) → limit(n); dropFirst(n) → skip(n)"], ["stream-basics", "optional-return"], ["streams"])

E("stream-collectors", "streams", "Dictionary(grouping:) / joined → Collectors",
  "Dictionary(grouping: people, by: { $0.city })", "collect(groupingBy(Person::city))",
  "Collectors build maps, sets and strings from streams.",
  "low", [r"Dictionary\s*\(\s*grouping:", r"Dictionary\s*\(\s*uniqueKeysWithValues:"],
  "let byCity = Dictionary(grouping: people, by: { $0.city })",
  "import static java.util.stream.Collectors.*;\nMap<String, List<Person>> byCity = people.stream().collect(groupingBy(Person::city));\nMap<String, Long> counts = people.stream().collect(groupingBy(Person::city, counting()));\nMap<String, Integer> nameToAge = people.stream().collect(toMap(Person::name, Person::age));\nString csv = names.stream().collect(joining(\", \"));",
  ["toMap throws on duplicate keys unless you pass a merge function.",
   "partitioningBy(pred) splits into Map<Boolean, List<T>>."],
  ["stream-basics", "string-building"], ["streams", "collectors"])

E("zip", "streams", "zip → no built-in; use an index range",
  "zip(a, b)", "IntStream.range(0, n).mapToObj(i -> …)",
  "Java streams have no zip. Iterate indices.",
  "low", [r"\bzip\s*\("],
  "for (x, y) in zip(xs, ys) { }",
  "int n = Math.min(xs.size(), ys.size());\nfor (int i = 0; i < n; i++) { var x = xs.get(i); var y = ys.get(i); }",
  [], ["enumerated-loops"], ["streams"])

# ---------------------------------------------------------------- functions
E("free-functions", "functions", "Top-level functions → static methods",
  "func greet(name: String) -> String", "public static String greet(String name)",
  "There are no free functions; put them as static methods on a final utility class. import static lets you call them unqualified.",
  "low", [r"^func\s+\w+"],
  "func greet(name: String) -> String { \"Hello, \\(name)\" }",
  "public final class Greetings {\n    private Greetings() {}\n    public static String greet(String name) { return \"Hello, \" + name; }\n}\n// import static com.example.Greetings.greet;",
  [], ["static-members", "extensions"], ["functions"])

E("argument-labels", "functions", "Argument labels → no labels (descriptive method names)",
  "move(from: a, to: b)", "move(a, b) / moveTo(…)",
  "Java has no argument labels. Put the meaning in the method name, or use a parameter record/builder.",
  "low", [r"\bfunc\s+\w+\s*(<[^>]*>)?\s*\(\s*[a-z]\w*\s+\w+\s*:"],
  "func move(from start: Point, to end: Point, animated: Bool = true)",
  "void move(Point start, Point end, boolean animated) { ... }\nvoid move(Point start, Point end) { move(start, end, true); }",
  ["Overloading by return type alone is not allowed in Java."],
  ["default-parameters"], ["functions", "api-design"])

E("varargs", "functions", "Variadic Int... → int...",
  "func sum(_ nums: Int...)", "static int sum(int... nums)",
  "Varargs work the same; inside the method the parameter is an array.",
  "low", [r"\w\.\.\.\s*[,)]"],
  "func sum(_ nums: Int...) -> Int",
  "static int sum(int... nums) {\n    int total = 0;\n    for (int n : nums) total += n;\n    return total;\n}",
  [], [], ["functions"])

E("inout", "functions", "inout → doesn't exist (return the new value)",
  "func reset(_ list: inout [String])", "return a new value instead",
  "Java passes everything by value; for objects the reference is copied. You can mutate the object but not reassign the caller's variable.",
  "high", [r"\binout\b", r"&\w+\s*[,)]"],
  "func increment(_ x: inout Int) { x += 1 }\nincrement(&count)",
  "int increment(int x) { return x + 1; }\ncount = increment(count);\n\nvoid addItem(List<String> list) { list.add(\"x\"); }         // caller sees it\nvoid reset(List<String> list) { list = new ArrayList<>(); } // caller unaffected",
  [], ["collection-types"], ["functions", "semantics"])

E("generic-methods", "functions", "Generic functions → <T> methods, constraints with extends",
  "func max<T: Comparable>(_ a: T, _ b: T) -> T", "static <T extends Comparable<T>> T max(T a, T b)",
  "Type parameters go before the return type; constraints use extends (for both classes and interfaces).",
  "low", [r"\bfunc\s+\w+\s*<"],
  "func firstOrDefault<T>(_ items: [T], _ fallback: T) -> T",
  "static <T> T firstOrDefault(List<T> items, T fallback) {\n    return items.isEmpty() ? fallback : items.getFirst();\n}\nstatic <T extends Comparable<T>> T max(T a, T b) {\n    return a.compareTo(b) >= 0 ? a : b;\n}",
  [], ["type-erasure", "associated-types"], ["generics", "functions"])

# ---------------------------------------------------------------- testing
E("junit-basics", "testing", "XCTest / Swift Testing → JUnit Jupiter",
  "XCTestCase, setUp(), XCTAssert…, @Test, #expect", "@Test, @BeforeEach, assertEquals…",
  "JUnit Jupiter is the standard. Any class can hold @Test methods; they don't need to be public or prefixed with test.",
  "low", [r"\bXCTestCase\b", r"\bXCTAssert\w*", r"@Test\b", r"#expect\b", r"@Suite\b"],
  "final class CalculatorTests: XCTestCase {\n    func testAdd() { XCTAssertEqual(calc.add(2, 3), 5) }\n}",
  "class CalculatorTest {\n    @BeforeEach void setUp() { calc = new Calculator(); }\n    @Test void adds() { assertEquals(5, calc.add(2, 3)); }\n}",
  ["setUp/tearDown → @BeforeEach/@AfterEach; class setUp → static @BeforeAll/@AfterAll",
   "XCTAssertNil → assertNull; XCTAssertTrue → assertTrue",
   "XCTAssertThrowsError / #expect(throws:) → assertThrows(Type.class, () -> …)",
   "@Test(arguments:) → @ParameterizedTest + @ValueSource/@CsvSource/@MethodSource",
   "XCTSkip / .disabled → @Disabled / assumeTrue(...)",
   "Tests live in src/test/java mirroring the main package.",
   "Companions: AssertJ (fluent assertions), Mockito (mocking)."],
  ["junit-assert-order"], ["testing"])

E("junit-assert-order", "testing", "assertEquals(expected, actual) — expected first",
  "XCTAssertEqual(actual, expected)", "assertEquals(expected, actual)",
  "JUnit puts the expected value first; swapping them produces misleading failure messages. Doubles need a delta.",
  "medium", [r"\bXCTAssertEqual\b", r"#expect\s*\([^)]*==", r"accuracy:"],
  "XCTAssertEqual(calc.add(2, 3), 5)\nXCTAssertEqual(x, 0.3, accuracy: 1e-9)",
  "assertEquals(5, calc.add(2, 3));\nassertEquals(0.3, calc.add(0.1, 0.2), 1e-9);\nassertAll(() -> assertEquals(\"Ana\", p.name()), () -> assertEquals(30, p.age()));",
  [], ["junit-basics"], ["testing"])

# ---------------------------------------------------------------- checklist
CHECKLIST = [
    ("int-width", "Int → int or long? Check the value ranges.", ["int-width", "integer-overflow"]),
    ("null-strategy", "Every optional (?) has an explicit null strategy (null check, Optional return, or non-null guarantee).", ["optional-type", "optional-binding", "optional-return"]),
    ("equals", "All == on strings, wrappers and objects replaced with .equals().", ["equality-operator", "boxed-types"]),
    ("structs", "Structs → records (or immutable classes), and code relying on copy-on-assign now copies explicitly.", ["struct-to-record", "collection-types"]),
    ("associated-enums", "Enums with associated values → sealed interface + records.", ["enum-associated-values"]),
    ("default-params", "Default parameter values → overloads or a builder.", ["default-parameters"]),
    ("extensions", "Extensions → static utility methods or interface default methods.", ["extensions", "protocols"]),
    ("cleanup", "deinit / defer → try-with-resources or finally.", ["deinit-autocloseable", "defer", "try-with-resources"]),
    ("captures", "Closures that mutate captured locals → restructured, or an atomic/holder used.", ["closure-capture-mutation"]),
    ("throws", "throws functions → checked or unchecked decision made deliberately.", ["throws-checked-unchecked", "throwing-closures"]),
    ("final", "Classes not intended for subclassing marked final.", ["open-by-default", "access-modifiers"]),
    ("hashing", "equals + hashCode implemented for anything used as a map key or in a set.", ["equatable-hashable"]),
    ("tests", "Tests moved from XCTest/Swift Testing to JUnit, with assertEquals(expected, actual) order fixed.", ["junit-basics", "junit-assert-order"]),
]


def build():
    ids = [m["id"] for m in M]
    assert len(ids) == len(set(ids)), "duplicate ids"
    cat_ids = {c[0] for c in CATEGORIES}
    errors = []
    for m in M:
        if m["category"] not in cat_ids:
            errors.append(f"{m['id']}: unknown category")
        for r in m["related"]:
            if r not in ids:
                errors.append(f"{m['id']}: unknown related {r}")
        for p in m["detect"]:
            try:
                re.compile(p, re.M)
            except re.error as e:
                errors.append(f"{m['id']}: bad regex {p}: {e}")
        if m["risk"] not in ("high", "medium", "low"):
            errors.append(f"{m['id']}: bad risk")
    for c in CHECKLIST:
        for r in c[2]:
            if r not in ids:
                errors.append(f"checklist {c[0]}: unknown mapping {r}")
    if errors:
        print("\n".join(errors)); sys.exit(1)
    data = {
        "guide": GUIDE,
        "categories": [{"id": c[0], "title": c[1], "summary": c[2],
                        "mappingCount": sum(1 for m in M if m["category"] == c[0])} for c in CATEGORIES],
        "mappings": M,
        "checklist": [{"id": c[0], "text": c[1], "mappingIds": c[2]} for c in CHECKLIST],
    }
    return data


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build()
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(data['mappings'])} mappings, {len(data['categories'])} categories, {len(data['checklist'])} checklist items -> {out}")
