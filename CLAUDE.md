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

### ⬜ 2. Read endpoints (mappings, categories/{id}, search, checklist, index)
- **Spring Boot:** `@PathVariable`, `@RequestParam` (optional values, defaults), Bean Validation (`@Min`/`@Max`, `@Validated`).
- **Java:** Streams for filtering and ranking, `Optional`.
- **Agent-first:** endpoints are shaped around tasks, not database tables. `relatedMappings` lets the agent move to related entries without guessing. `GET /api` describes every endpoint so the API can be discovered with no outside docs. Search accepts raw syntax (`??`, `$0`), which is what an agent actually has in hand.

### ⬜ 3. `POST /api/analyze`
- **Spring Boot:** `@RequestBody`, accepting more than one content type (`consumes`), `ResponseEntity`, request size limits.
- **Agent-first:** accept input in whatever form is easiest for the agent to send (raw text or JSON). Findings come with line numbers and are ordered by risk, so they can be acted on directly. The response says plainly that detection may produce false positives.

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
