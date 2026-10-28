package com.carolinabarreiro.swifttojava.guide;

import com.fasterxml.jackson.annotation.JsonUnwrapped;

import java.util.List;

record CategoryResponse(@JsonUnwrapped Guide.Category category, List<Guide.Mapping> mappings) {
}
