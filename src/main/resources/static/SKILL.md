---
name: swift-to-java
description: Use when converting Swift code to Java, reviewing a Swift-to-Java port, or answering "what is the Java equivalent of <Swift idiom>". Looks up curated, deterministic mappings (with pitfalls) from the Swift to Java Conversion Guide API instead of guessing.
---

# Swift → Java conversion

A public, zero-auth API at `{{BASE_URL}}` holds curated Swift → Java 21 mappings: each one has the Java equivalent, examples on both sides, a risk level and the pitfalls that cause real bugs. Use it as the source of truth for idioms; you still write the Java yourself.

## When to use

- The user asks you to port, translate or rewrite Swift code in Java.
- The user is a Swift developer asking how something works in Java ("guard let in Java?", "Java structs?").
- You are reviewing Java code that was converted from Swift.

Don't use it for general Java questions with no Swift angle.

## Decision tree

1. **Have Swift source?** → `POST {{BASE_URL}}/api/analyze?format=md` with the source as `text/plain`.
   - Work through findings **high → medium → low**. High-risk findings are where ports silently break (`==` vs `.equals()`, struct value semantics, optionals, `inout`, checked exceptions).
   - Each finding lists the Swift lines it matched. Apply that mapping's Java pattern to those lines.
   - Finish with the returned checklist items.
2. **Asking about one idiom?** → `GET {{BASE_URL}}/api/search?q=<idiom>&format=md`. Raw Swift syntax works: `q=??`, `q=$0`, `q=guard let`, `q=inout`.
3. **Need the full entry?** → `GET {{BASE_URL}}/api/mappings/{id}?format=md` (also lists related mappings).
4. **Before you say the port is done** → `GET {{BASE_URL}}/api/checklist?format=md` and check every item.

## Guardrails

- Prefer the API's mapping over your own recall when they disagree; it is pinned to **Java 21**. Note any `since` field (e.g. Java 21, Java 22+) before using a feature.
- Detection is pattern-based: a finding can be a false positive. Read the matched line before applying.
- Don't invent mapping ids. If `GET /api/mappings/{id}` returns 404, use the `suggestions` in the error body or `/api/search`.
- Never translate `==` on objects, strings or wrappers to `==` in Java. Use `.equals()` / `Objects.equals()`.
- Swift structs and collections copy on assignment; Java ones do not. Copy explicitly or keep the type immutable.

## Offline fallback (API unreachable)

The highest-risk mappings, in brief:

- `a == b` (objects/strings/Integer) → `a.equals(b)` / `Objects.equals(a, b)`
- `struct` → `record` (still a reference; immutability gives value semantics)
- `T?` → nullable reference; `Optional<T>` only as a return type; `??` → `Objects.requireNonNullElse`
- `[T]` / `[K: V]` → `List<T>` / `Map<K, V>`: assignment shares, so `new ArrayList<>(a)` to copy
- `inout` → return the new value
- `throws` → choose checked (`extends Exception`) or unchecked (`extends RuntimeException`)
- `Int("42")` → `Integer.parseInt("42")`, which throws `NumberFormatException`
- `deinit` → `AutoCloseable` + try-with-resources
- `Hashable` → override `equals` **and** `hashCode` (or use a record)
- Integer overflow wraps silently; use `Math.addExact` where it matters
