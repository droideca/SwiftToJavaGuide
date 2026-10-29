# SwiftToJava

An **agent-first API** built from the "Swift to Java" conversion guide. Basically we assume an AI coding agent uses the API first and a person second, so it has to be standardized, fast and well documented.

## Who I am and how to work with me

- I'm a Swift (iOS) developer learning Java and Spring for backend work. This project is a learning exercise as much as a product.
- When you introduce a Spring or Java concept, explain it briefly. Only compare it to Swift if I ask.
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

Packages are organized by feature, one type per file.

Ported from the reference (package renamed, otherwise unchanged):
- `guide/Guide.java`: loads `resources/data/mappings.json` into records (Mapping, Category, ChecklistItem, Risk enum)
- `guide/Search.java`: ranked search. Accepts concepts or raw Swift syntax (`??`, `$0`, `guard let`).
- `guide/Json.java`: hand-written JSON parser, used only by `Guide` to load the dataset. Replace it with Jackson later.
- `analyze/Analyzer.java`: regex-based Swift construct detection → findings by line, ordered by risk
- `docs/Docs.java`: Markdown renderings (llms.txt, llms-full.txt, a single mapping, analyze report)
- `resources/static/`: `index.html` (human page), `SKILL.md` and `openapi.json`. The last two contain a `{{BASE_URL}}` placeholder that must be filled in per request.

Built in this project:
- `guide/GuideConfig.java` provides `Guide` and `Search` as beans; `analyze/AnalyzeConfig.java` provides `Analyzer`.
- `guide/GuideController.java` serves every read endpoint: `/api`, `/api/guide`, `/api/categories`, `/api/categories/{id}`, `/api/mappings`, `/api/mappings/{id}`, `/api/search`, `/api/checklist`.
- `guide/*Response.java` and `guide/RelatedMapping.java`: response records. `ApiIndexResponse` is the response of `GET /api` (docs links, endpoint list, stats).
- `analyze/AnalyzeController.java`: `POST /api/analyze`, with three handlers on the same path:
  - JSON `{"code": ...}`
  - form-urlencoded (what `curl --data-binary` sends without `-H`), read as raw bytes
  - everything else, treated as raw text
  - All three share the blank check (400) and the 200 KB limit (413).
- `application.properties`: Jackson writes enums in lowercase and omits `null` fields, to match the reference.
- `AnalyzeConfig.strictStrings()`: a `JsonMapperBuilderCustomizer` so request bodies reject numbers and booleans in `String` fields. It's app-wide, so move it to a shared config package in step 6 or 7.
- Errors so far are plain `ResponseStatusException`s or Bean Validation failures. The status codes are correct, but the bodies don't match the reference yet (step 6).
- Not checked by automated tests yet (step 8). Each endpoint was verified by diffing its responses against the reference server.

Deliberately NOT ported: `Server.java` (to be rebuilt as controllers), `SelfTest.java` (to become JUnit tests), `run.sh` and `Dockerfile`.

## Port plan (in order)

1. `GET /api/guide`: the whole dataset. This makes `index.html` work.
2. `GET /api/mappings` (filters: `category`, `risk`, `tag`), `GET /api/mappings/{id}` (with `relatedMappings`), `GET /api/categories/{id}`, `GET /api/search?q=&limit=` (1–50, default 5), `GET /api/checklist`, `GET /api` (endpoint index)
3. `POST /api/analyze`: body is `text/plain` Swift source or JSON `{"code": "..."}`, max 200 KB
4. `?format=md` → `text/markdown` responses via `Docs`
5. `/llms.txt`, `/llms-full.txt`, `/SKILL.md`, `/openapi.json` with `{{BASE_URL}}` filled from the request (or a `BASE_URL` env var)
6. Errors → `ProblemDetail` (`application/problem+json`) through `@RestControllerAdvice`, keeping the extra `hint`, `example` and `suggestions` fields (an unknown mapping id suggests the closest ids via `Search`)
7. CORS `*` and `Cache-Control: public, max-age=3600` on GETs. Also accept trailing slashes (`/api/`, `/api/guide/`) like the reference does; Spring Boot 4 returns 404 for them by default.
8. Port `SelfTest` to JUnit 5 + MockMvc
9. Later: Jackson instead of `Json.java`, springdoc for OpenAPI, deployment, possibly an MCP server

## Learning log

What each step teaches about building a Spring Boot backend meant to be used by AI agents first.
When a step is finished, mark it ✅ and note what actually came up.
Status: ✅ done · 🔄 in progress · ⬜ not started

### ✅ 0. Project setup and porting the core
- **Spring Boot:** Initializr, Gradle Kotlin DSL, Java toolchains, `@SpringBootApplication` and the embedded server, `src/main/resources` and the classpath.
- **Java:** records as immutable DTOs, enums, loading a dataset once at startup.
- **Agent-first:** the dataset is the product. A stable, machine-readable model (`mappings.json` → records) comes before any endpoint.

### ✅ 0b. First endpoint: `GET /api/categories`
- **Spring Boot:** the IoC container, `@Configuration` + `@Bean`, constructor injection, `@RestController` / `@GetMapping`, automatic JSON serialization with Jackson.
- **Agent-first:** responses are wrapped in a named object (`{"categories": [...]}`), not a bare array, so fields can be added later without breaking clients.

### ✅ 1. `GET /api/guide`
- **Spring Boot:** how Jackson serializes nested records; customizing it (lowercase enums, field naming) through configuration instead of annotations everywhere.
- **Agent-first:** one call returns everything. An agent can load the whole dataset into context instead of making N requests.
- **What came up:**
  - A response record (`GuideResponse`) instead of a `Map`: typed, fixed key order, shape declared in one place.
  - Spring Boot 4 uses Jackson 3, so Jackson 2 tutorials can be wrong. I checked property names against the actual jars.
  - Two global properties: `spring.jackson.datatype.enum.write-enums-to-lowercase=true` and `spring.jackson.default-property-inclusion=non_null`. The reference omits `null` fields, but Jackson writes them by default. Pick one convention ("absent" vs `null`) and keep it.
  - Verified by diffing the response against the reference server field by field.
  - Moved the guide classes into a `guide/` package (package by feature). IntelliJ's move refactoring rewrote `Guide.Info` as `guide.Info`, so check the compile after a move.

### ✅ 2. Read endpoints (mappings, categories/{id}, search, checklist, index)
- **Spring Boot:** `@PathVariable`, `@RequestParam` (optional values, defaults), Bean Validation (`@Min`/`@Max`, `@Validated`).
- **Java:** Streams for filtering and ranking, `Optional`.
- **Agent-first:** endpoints are shaped around tasks, not database tables. `relatedMappings` lets the agent move to related entries without guessing. `GET /api` describes every endpoint so the API can be discovered with no outside docs. Search accepts raw syntax (`??`, `$0`), which is what an agent actually has in hand.
- **What came up:**
  - `@PathVariable` reads `/categories/{id}`; `@RequestParam` reads `?id=`. Mixing them up gives a 400 for a perfectly good URL.
  - Optional parameters have three states: absent (`null`, so don't filter), present and valid, present and invalid (400). Treating "absent" as "invalid" was the main bug. Use `required = false` for "no filter", `defaultValue` when absent means a specific value (`limit=5`), and required when the endpoint is meaningless without it (`q`).
  - A lookup that returns `null` becomes an empty 200 unless you check it. For an agent that's the worst answer, so return a 404. In the same way, an unknown filter value gets a 400 instead of `"count": 0`.
  - Checked vs unchecked exceptions: `valueOf`, NPE and `ResponseStatusException` are unchecked, so the compiler doesn't warn you. Anything uncaught becomes a 500.
  - `Enum.valueOf` matches the constant name exactly and throws. Normalize with `toUpperCase(Locale.ROOT)` and catch the exception.
  - `@JsonUnwrapped` flattens a record's fields into the response (`CategoryResponse`, `MappingResponse`) without copying them. Its import stays `com.fasterxml.jackson.annotation` in Jackson 3.
  - Records: static factories (`of`), extra constructors that must call `this(...)` first, nested records for parts of a response (`ApiIndexResponse.Docs`).
  - Streams with method references: `related().stream().map(guide::mapping).filter(Objects::nonNull).map(RelatedMapping::of).toList()`.
  - `@Bean` methods can take other beans as parameters, and Spring wires the graph `Guide` → `Analyzer` → `Search` → controller.
  - Bean Validation (`@NotBlank`, `@Min`, `@Max`) works on controller parameters with no extra setup. The error messages are Spring's generic ones, though, and step 6 has to translate them. `@RequestParam` alone accepts `q=`, so you also need `@NotBlank`.
  - REST paths: plural for both the collection and one item (`/mappings`, `/mappings/{id}`). A singular `/mapping/{id}` breaks every `detailUrl`.
  - `ServletUriComponentsBuilder.fromCurrentContextPath()` gives the base URL of the current request (used for the `docs` links in `GET /api`).
  - Contract details that are easy to miss: exact `hint` texts, `count` before the list, an empty list rather than a missing one.

### ✅ 3. `POST /api/analyze`
- **Spring Boot:** `@RequestBody`, accepting more than one content type (`consumes`), `ResponseEntity`, request size limits.
- **Agent-first:** accept input in whatever form is easiest for the agent to send (raw text or JSON). Findings come with line numbers and are ordered by risk, so they can be acted on directly. The response says plainly that detection may produce false positives.
- **What came up:**
  - `@RequestBody String` gives the raw text; `@RequestBody SomeRecord` makes Jackson parse JSON into the record.
  - Several handlers can share one path. Spring picks the most specific `consumes` match, and a handler without `consumes` catches everything else, including a missing `Content-Type`.
  - Body validation has three layers:
    - Jackson syntax/shape errors are an automatic 400.
    - `@Valid` + `@NotBlank` on the record's fields covers `{}`, `null` and `""`.
    - Type coercion: Jackson silently turns `42`/`true` into `"42"`/`"true"`. `ALLOW_COERCION_OF_SCALARS` does not stop it for `String`; a coercion config in a `JsonMapperBuilderCustomizer` bean does.
  - **The curl trap:** `curl --data-binary @File.swift` without `-H` sends `application/x-www-form-urlencoded`. Spring then hands `@RequestBody String` the body re-encoded as form fields (`let+n+=+Int%28...`), and the result is a 200 with a wrong report. That's the worst failure for an agent because nothing signals it. Fix: a dedicated handler that reads the raw bytes via `HttpServletRequest.getInputStream()`.
  - `getInputStream()` throws `IOException`, the first checked exception in the project, so the method needs `throws IOException`.
  - Size limits count bytes (`getBytes(UTF_8).length`), not characters. Spring has no default limit for a normal request body.
  - One private `validateAndAnalyze` holds the shared rules, so the three entry points can't drift apart.
  - `static` is allowed on fields, not on local variables. Constants are `static final UPPER_SNAKE_CASE` at the top of the class.
  - IntelliJ's Extract Method can add JSpecify `@NonNull` (written `Analyzer.@NonNull Report` for a nested type). Adopt it project-wide or not at all.
  - `@Bean` placement: beans can live in any `@Configuration` under the main package and be injected across packages (`Search` in `guide` gets `Analyzer` from `analyze`).
  - Verified with 20 cases against the reference: text, JSON, form, Unicode, every 400, every 413, no content type, XML.

### ⬜ 4. `?format=md`
- **Spring Boot:** content negotiation, `produces`, `MediaType`, returning `String` bodies with a custom `Content-Type`.
- **Agent-first:** Markdown costs fewer tokens and LLMs read it well. JSON is for code, Markdown is for a model's context, and both come from the same endpoint.

### ⬜ 5. `/llms.txt`, `/llms-full.txt`, `/SKILL.md`, `/openapi.json`
- **Spring Boot:** static vs dynamic resources, reading the request URL (`ServletUriComponentsBuilder`), externalized config (`@Value`, env vars, `application.properties`).
- **Agent-first:** the conventions agents look for (llms.txt, skills, OpenAPI), with absolute URLs filled in for wherever the API is deployed, so the agent never builds a link to the wrong host.

### ⬜ 6. Errors as `ProblemDetail`
- **Spring Boot:** custom exceptions, `@RestControllerAdvice` + `@ExceptionHandler`, `ProblemDetail` (RFC 9457) with extra properties.
- **Java:** checked vs unchecked exceptions.
- **Agent-first:** every error tells the agent how to recover: a `hint`, a valid `example`, and `suggestions` (closest ids for an unknown mapping). An agent can fix the request and retry without a human.

### ⬜ 7. CORS and caching headers
- **Spring Boot:** `WebMvcConfigurer` for global CORS, filters/interceptors for headers that apply to every response.
- **Agent-first:** no auth and open CORS, so any agent or browser tool can call the API. Caching makes repeated reads cheap and fast.

### ⬜ 8. Tests with JUnit 5 + MockMvc
- **Spring Boot:** `@SpringBootTest` vs `@WebMvcTest`, MockMvc, `jsonPath` assertions, test slices.
- **Agent-first:** the HTTP contract (field names, status codes, error shape) is what agents depend on, so it is what gets tested. Any change to it is a breaking change.

### ⬜ 9. Later
- **Spring Boot:** replace `Json.java` with Jackson `ObjectMapper`; springdoc to generate OpenAPI from code; packaging (`bootJar`), Docker, deployment config.
- **Agent-first:** an MCP server on top of the same `Guide`, exposing the API as tools that agents can call natively.

## Conventions (keep these, they are the point of the project)

- JSON field names and values must stay identical to the reference version. Risk values are lowercase (`"high"`, not `"HIGH"`), so configure Jackson accordingly.
- Every error tells the caller how to fix the request (`hint`), with a valid `example` where useful.
- No auth. Endpoints are task-shaped, not table-shaped.
- Content changes go through `tools/build_data.py` (one `E(...)` per mapping), never by hand-editing `mappings.json`. Regenerate with `python3 tools/build_data.py src/main/resources/data/mappings.json`. Every mapping's own `swiftExample` must be caught by its `detect` patterns.
- Detection is pattern-based and may produce false positives; responses say so.
