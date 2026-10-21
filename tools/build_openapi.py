"""Generates src/main/resources/static/openapi.json ({{BASE_URL}} is filled in at request time)."""
import json, pathlib, sys

risk = {"type": "string", "enum": ["high", "medium", "low"]}
fmt = {"name": "format", "in": "query", "required": False,
       "description": "Set to `md` for a Markdown response that can be pasted into an LLM context.",
       "schema": {"type": "string", "enum": ["json", "md"]}}

def ref(n): return {"$ref": f"#/components/schemas/{n}"}
def ok(schema, md=True):
    content = {"application/json": {"schema": schema}}
    if md: content["text/markdown"] = {"schema": {"type": "string"}}
    return {"200": {"description": "OK", "content": content}}
problem = {"description": "Problem details with a `hint` explaining how to fix the request.",
           "content": {"application/problem+json": {"schema": ref("Problem")}}}

spec = {
  "openapi": "3.1.0",
  "info": {
    "title": "Swift to Java Conversion Guide API",
    "version": "1.0.0",
    "description": "Curated, deterministic Swift → Java 21 mappings for AI agents and developers. "
                   "No auth. Start with POST /api/analyze for Swift source, or GET /api/search for a single idiom. "
                   "Guidance for agents: {{BASE_URL}}/llms.txt"
  },
  "servers": [{"url": "{{BASE_URL}}"}],
  "paths": {
    "/api/analyze": {"post": {
      "operationId": "analyzeSwift",
      "summary": "Detect Swift constructs in source code and return the matching Java mappings",
      "description": "Pattern-based detection (may include false positives). Findings are ordered by risk (high first), then by line. Max body 200 KB.",
      "parameters": [fmt],
      "requestBody": {"required": True, "content": {
        "text/plain": {"schema": {"type": "string"}, "example": "guard let user = user else { return }\nlet name = user.name ?? \"Unknown\""},
        "application/json": {"schema": {"type": "object", "required": ["code"], "properties": {"code": {"type": "string"}}}}}},
      "responses": {**ok(ref("Report")), "400": problem, "413": problem}}},
    "/api/search": {"get": {
      "operationId": "searchMappings",
      "summary": "Ranked search by concept or raw Swift syntax",
      "parameters": [
        {"name": "q", "in": "query", "required": True, "schema": {"type": "string"},
         "description": "Concept or Swift syntax, e.g. `guard let`, `??`, `$0`, `inout`, `default parameters`.", "example": "guard let"},
        {"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5}}, fmt],
      "responses": {**ok({"type": "object", "properties": {
          "query": {"type": "string"}, "count": {"type": "integer"},
          "results": {"type": "array", "items": ref("SearchHit")}, "hint": {"type": "string"}}}), "400": problem}}},
    "/api/mappings": {"get": {
      "operationId": "listMappings", "summary": "List and filter mappings",
      "parameters": [
        {"name": "category", "in": "query", "schema": {"type": "string"}, "description": "Category id from /api/categories."},
        {"name": "risk", "in": "query", "schema": risk},
        {"name": "tag", "in": "query", "schema": {"type": "string"}, "description": "Tag, e.g. optionals, equality, generics."}, fmt],
      "responses": {**ok({"type": "object", "properties": {"count": {"type": "integer"},
          "mappings": {"type": "array", "items": ref("Mapping")}}}), "400": problem}}},
    "/api/mappings/{id}": {"get": {
      "operationId": "getMapping", "summary": "One mapping with examples, pitfalls and related mappings",
      "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}, "example": "optional-binding"}, fmt],
      "responses": {**ok(ref("Mapping")), "404": {"description": "Unknown id. The body includes `suggestions`.",
          "content": {"application/problem+json": {"schema": ref("Problem")}}}}}},
    "/api/categories": {"get": {
      "operationId": "listCategories", "summary": "Categories with mapping counts",
      "responses": ok({"type": "object", "properties": {"categories": {"type": "array", "items": ref("Category")}}}, md=False)}},
    "/api/categories/{id}": {"get": {
      "operationId": "getCategory", "summary": "One category with its mappings",
      "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}, "example": "strings"}, fmt],
      "responses": {**ok(ref("Category")), "404": problem}}},
    "/api/checklist": {"get": {
      "operationId": "getChecklist", "summary": "Final review checklist for a Swift → Java port",
      "parameters": [fmt],
      "responses": ok({"type": "object", "properties": {"checklist": {"type": "array", "items": ref("ChecklistItem")}}})}},
    "/api/guide": {"get": {
      "operationId": "getGuide", "summary": "The whole dataset in one response",
      "responses": ok({"type": "object"}, md=False)}},
  },
  "components": {"schemas": {
    "Mapping": {"type": "object", "required": ["id", "category", "title", "swift", "java", "summary", "risk"], "properties": {
      "id": {"type": "string"}, "category": {"type": "string"}, "title": {"type": "string"},
      "swift": {"type": "string", "description": "The Swift construct"},
      "java": {"type": "string", "description": "The Java equivalent"},
      "summary": {"type": "string"}, "risk": risk,
      "detect": {"type": "array", "items": {"type": "string"}, "description": "Regexes used by /api/analyze"},
      "swiftExample": {"type": "string"}, "javaExample": {"type": "string"},
      "gotchas": {"type": "array", "items": {"type": "string"}},
      "related": {"type": "array", "items": {"type": "string"}},
      "tags": {"type": "array", "items": {"type": "string"}},
      "since": {"type": "string", "description": "Minimum Java version when above the baseline"}}},
    "SearchHit": {"type": "object", "properties": {
      "id": {"type": "string"}, "title": {"type": "string"}, "risk": risk, "category": {"type": "string"},
      "swift": {"type": "string"}, "java": {"type": "string"}, "summary": {"type": "string"},
      "score": {"type": "number"}, "detailUrl": {"type": "string"}}},
    "Category": {"type": "object", "properties": {
      "id": {"type": "string"}, "title": {"type": "string"}, "summary": {"type": "string"}, "mappingCount": {"type": "integer"}}},
    "ChecklistItem": {"type": "object", "properties": {
      "id": {"type": "string"}, "text": {"type": "string"}, "mappingIds": {"type": "array", "items": {"type": "string"}}}},
    "Report": {"type": "object", "properties": {
      "summary": {"type": "object", "properties": {
        "linesAnalyzed": {"type": "integer"}, "constructsFound": {"type": "integer"},
        "byRisk": {"type": "object", "additionalProperties": {"type": "integer"}}}},
      "findings": {"type": "array", "items": {"type": "object", "properties": {
        "mappingId": {"type": "string"}, "title": {"type": "string"}, "risk": risk, "category": {"type": "string"},
        "swift": {"type": "string"}, "java": {"type": "string"}, "summary": {"type": "string"},
        "gotchas": {"type": "array", "items": {"type": "string"}},
        "occurrences": {"type": "integer"},
        "lines": {"type": "array", "items": {"type": "object", "properties": {
          "line": {"type": "integer"}, "code": {"type": "string"}}}},
        "detailUrl": {"type": "string"}}}},
      "checklist": {"type": "array", "items": ref("ChecklistItem")},
      "note": {"type": "string"}}},
    "Problem": {"type": "object", "properties": {
      "type": {"type": "string"}, "title": {"type": "string"}, "status": {"type": "integer"},
      "detail": {"type": "string"}, "hint": {"type": "string", "description": "How to fix the request"},
      "example": {"type": "string", "description": "A valid example request"},
      "suggestions": {"type": "array", "items": {"type": "string"}}}},
  }},
}

out = pathlib.Path(sys.argv[1])
out.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("wrote", out)
