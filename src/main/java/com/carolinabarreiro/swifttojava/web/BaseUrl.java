package com.carolinabarreiro.swifttojava.web;

import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

/** The public base URL used in absolute links: the BASE_URL setting if present, otherwise the current request's. */
public final class BaseUrl {

    private final String configured;

    BaseUrl(String configured) {
        this.configured = configured == null || configured.isBlank() ? null : configured.replaceAll("/$", "");
    }

    public String get() {
        return configured != null ? configured : ServletUriComponentsBuilder.fromCurrentContextPath().toUriString();
    }
}
