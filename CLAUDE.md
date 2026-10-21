# SwiftToJava

An **agent-first API** built from the "Swift to Java" conversion guide. Basically we assume an AI coding agent uses the API first and a person second, so it has to be standardized, fast and well documented.

## Who I am and how to work with me

- I'm a Swift (iOS) developer learning Java and Spring for backend work. This project is a learning exercise as much as a product.
- When you introduce a Spring or Java concept, explain it briefly and compare it to the Swift equivalent where there is one.
- Prefer small, reviewable steps. Tell me what you changed and why.

## Stack

- Spring Boot 4.1.x, Java 21 (Gradle toolchain), Gradle Kotlin DSL
- Dependencies: spring-boot-starter-webmvc, spring-boot-starter-validation, devtools
- Package: `com.carolinabarreiro.swifttojava`
- Run: `./gradlew bootRun` (or ▶ on `SwiftToJavaApplication` in IntelliJ). Test: `./gradlew test`

## Reference implementation

`~/Developer/swift-java-api` is the original zero-dependency version: plain Java 21 with the JDK `HttpServer`. It is complete and tested, so use it as the spec for behavior.

- `src/main/java/dev/swiftjava/Server.java`: all routes, query params, error bodies and `?format=md` handling
- `src/test/java/dev/swiftjava/SelfTest.java`: the expected HTTP contract, already written in JUnit style
- Its README explains how each piece relates to the agent-first principles

## Current state of this project

Ported as-is (package renamed, otherwise unchanged):
- `Guide.java`: loads `resources/data/mappings.json` into records (Mapping, Category, ChecklistItem, Risk enum)
- `Analyzer.java`: regex-based Swift construct detection → findings by line, ordered by risk
- `Search.java`: ranked search. Accepts concepts or raw Swift syntax (`??`, `$0`, `guard let`).
- `Docs.java`: Markdown renderings (llms.txt, llms-full.txt, a single mapping, analyze report)
- `Json.java`: hand-written JSON parser, used only by `Guide` to load the dataset. Replace it with Jackson later.
- `resources/static/`: `index.html` (human page), `SKILL.md` and `openapi.json`. The last two contain a `{{BASE_URL}}` placeholder that must be filled in per request.
- `GuideController.java`: `GuideConfig` provides `Guide` as a bean; only `GET /api/categories` exists so far.

Deliberately NOT ported: `Server.java` (to be rebuilt as controllers), `SelfTest.java` (to become JUnit tests), `run.sh` and `Dockerfile`.

## Port plan (in order)

1. `GET /api/guide`: the whole dataset. This makes `index.html` work.
2. `GET /api/mappings` (filters: `category`, `risk`, `tag`), `GET /api/mappings/{id}` (with `relatedMappings`), `GET /api/categories/{id}`, `GET /api/search?q=&limit=` (1–50, default 5), `GET /api/checklist`, `GET /api` (endpoint index)
3. `POST /api/analyze`: body is `text/plain` Swift source or JSON `{"code": "..."}`, max 200 KB
4. `?format=md` → `text/markdown` responses via `Docs`
5. `/llms.txt`, `/llms-full.txt`, `/SKILL.md`, `/openapi.json` with `{{BASE_URL}}` filled from the request (or a `BASE_URL` env var)
6. Errors → `ProblemDetail` (`application/problem+json`) through `@RestControllerAdvice`, keeping the extra `hint`, `example` and `suggestions` fields (an unknown mapping id suggests the closest ids via `Search`)
7. CORS `*` and `Cache-Control: public, max-age=3600` on GETs
8. Port `SelfTest` to JUnit 5 + MockMvc
9. Later: Jackson instead of `Json.java`, springdoc for OpenAPI, deployment, possibly an MCP server

## Conventions (keep these, they are the point of the project)

- JSON field names and values must stay identical to the reference version. Risk values are lowercase (`"high"`, not `"HIGH"`), so configure Jackson accordingly.
- Every error tells the caller how to fix the request (`hint`), with a valid `example` where useful.
- No auth. Endpoints are task-shaped, not table-shaped.
- Content changes go through `tools/build_data.py` (one `E(...)` per mapping), never by hand-editing `mappings.json`. Regenerate with `python3 tools/build_data.py src/main/resources/data/mappings.json`. Every mapping's own `swiftExample` must be caught by its `detect` patterns.
- Detection is pattern-based and may produce false positives; responses say so.
