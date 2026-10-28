package com.carolinabarreiro.swifttojava.guide;

import java.lang.reflect.RecordComponent;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Minimal JSON reader/writer so the project needs no dependencies.
 * Reading produces Map / List / String / Double / Long / Boolean / null.
 * Writing accepts those plus Java records (serialized by their components).
 */
public final class Json {
    private Json() {}

    // ------------------------------------------------------------------ write

    public static String write(Object value) {
        var sb = new StringBuilder();
        write(value, sb, 0, true);
        return sb.toString();
    }

    private static void write(Object v, StringBuilder sb, int indent, boolean pretty) {
        switch (v) {
            case null -> sb.append("null");
            case String s -> quote(s, sb);
            case Boolean b -> sb.append(b);
            case Integer i -> sb.append(i);
            case Long l -> sb.append(l);
            case Double d -> sb.append(d == Math.rint(d) && !Double.isInfinite(d) ? String.valueOf(d.longValue()) : d.toString());
            case Number n -> sb.append(n);
            case Map<?, ?> m -> writeObject(m, sb, indent, pretty);
            case Collection<?> c -> writeArray(c, sb, indent, pretty);
            case Record r -> writeObject(recordToMap(r), sb, indent, pretty);
            case Enum<?> e -> quote(e.name().toLowerCase(), sb);
            default -> quote(v.toString(), sb);
        }
    }

    /** Records become ordered maps of their components; null components are skipped. */
    public static Map<String, Object> recordToMap(Record r) {
        var map = new LinkedHashMap<String, Object>();
        for (RecordComponent rc : r.getClass().getRecordComponents()) {
            try {
                Object value = rc.getAccessor().invoke(r);
                if (value != null) map.put(rc.getName(), value);
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException(e);
            }
        }
        return map;
    }

    private static void writeObject(Map<?, ?> m, StringBuilder sb, int indent, boolean pretty) {
        if (m.isEmpty()) { sb.append("{}"); return; }
        sb.append('{');
        boolean first = true;
        for (var e : m.entrySet()) {
            if (!first) sb.append(',');
            first = false;
            newline(sb, indent + 1, pretty);
            quote(String.valueOf(e.getKey()), sb);
            sb.append(pretty ? ": " : ":");
            write(e.getValue(), sb, indent + 1, pretty);
        }
        newline(sb, indent, pretty);
        sb.append('}');
    }

    private static void writeArray(Collection<?> c, StringBuilder sb, int indent, boolean pretty) {
        if (c.isEmpty()) { sb.append("[]"); return; }
        boolean simple = c.stream().allMatch(x -> x == null || x instanceof String || x instanceof Number || x instanceof Boolean);
        sb.append('[');
        boolean first = true;
        for (Object item : c) {
            if (!first) sb.append(simple && pretty ? ", " : ",");
            first = false;
            if (!simple) newline(sb, indent + 1, pretty);
            write(item, sb, indent + 1, pretty);
        }
        if (!simple) newline(sb, indent, pretty);
        sb.append(']');
    }

    private static void newline(StringBuilder sb, int indent, boolean pretty) {
        if (!pretty) return;
        sb.append('\n');
        sb.append("  ".repeat(indent));
    }

    private static void quote(String s, StringBuilder sb) {
        sb.append('"');
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            switch (ch) {
                case '"' -> sb.append("\\\"");
                case '\\' -> sb.append("\\\\");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> {
                    if (ch < 0x20) sb.append("\\u%04x".formatted((int) ch));
                    else sb.append(ch);
                }
            }
        }
        sb.append('"');
    }

    // ------------------------------------------------------------------ read

    public static Object parse(String text) {
        var p = new Parser(text);
        p.skipWs();
        Object v = p.value();
        p.skipWs();
        if (p.pos != text.length()) throw p.error("Unexpected trailing content");
        return v;
    }

    private static final class Parser {
        private final String s;
        private int pos;

        Parser(String s) { this.s = s; }

        IllegalArgumentException error(String msg) {
            return new IllegalArgumentException(msg + " at position " + pos);
        }

        void skipWs() {
            while (pos < s.length() && Character.isWhitespace(s.charAt(pos))) pos++;
        }

        Object value() {
            if (pos >= s.length()) throw error("Unexpected end of input");
            char c = s.charAt(pos);
            return switch (c) {
                case '{' -> object();
                case '[' -> array();
                case '"' -> string();
                case 't' -> literal("true", Boolean.TRUE);
                case 'f' -> literal("false", Boolean.FALSE);
                case 'n' -> literal("null", null);
                default -> number();
            };
        }

        Object literal(String word, Object result) {
            if (!s.startsWith(word, pos)) throw error("Invalid literal");
            pos += word.length();
            return result;
        }

        Map<String, Object> object() {
            var map = new LinkedHashMap<String, Object>();
            pos++; // {
            skipWs();
            if (peek('}')) { pos++; return map; }
            while (true) {
                skipWs();
                if (!peek('"')) throw error("Expected string key");
                String key = string();
                skipWs();
                expect(':');
                skipWs();
                map.put(key, value());
                skipWs();
                if (peek(',')) { pos++; continue; }
                expect('}');
                return map;
            }
        }

        List<Object> array() {
            var list = new ArrayList<Object>();
            pos++; // [
            skipWs();
            if (peek(']')) { pos++; return list; }
            while (true) {
                skipWs();
                list.add(value());
                skipWs();
                if (peek(',')) { pos++; continue; }
                expect(']');
                return list;
            }
        }

        String string() {
            expect('"');
            var sb = new StringBuilder();
            while (true) {
                if (pos >= s.length()) throw error("Unterminated string");
                char c = s.charAt(pos++);
                if (c == '"') return sb.toString();
                if (c != '\\') { sb.append(c); continue; }
                char e = s.charAt(pos++);
                switch (e) {
                    case '"', '\\', '/' -> sb.append(e);
                    case 'n' -> sb.append('\n');
                    case 't' -> sb.append('\t');
                    case 'r' -> sb.append('\r');
                    case 'b' -> sb.append('\b');
                    case 'f' -> sb.append('\f');
                    case 'u' -> {
                        sb.append((char) Integer.parseInt(s.substring(pos, pos + 4), 16));
                        pos += 4;
                    }
                    default -> throw error("Invalid escape \\" + e);
                }
            }
        }

        Object number() {
            int start = pos;
            while (pos < s.length() && "+-0123456789.eE".indexOf(s.charAt(pos)) >= 0) pos++;
            String n = s.substring(start, pos);
            if (n.isEmpty()) throw error("Unexpected character '" + s.charAt(pos) + "'");
            try {
                return (n.contains(".") || n.contains("e") || n.contains("E")) ? (Object) Double.parseDouble(n) : (Object) Long.parseLong(n);
            } catch (NumberFormatException ex) {
                throw error("Invalid number " + n);
            }
        }

        boolean peek(char c) { return pos < s.length() && s.charAt(pos) == c; }

        void expect(char c) {
            if (!peek(c)) throw error("Expected '" + c + "'");
            pos++;
        }
    }
}
