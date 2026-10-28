package com.carolinabarreiro.swifttojava.guide;

import java.util.List;

record GuideResponse(
        Guide.Info guide,
        List<Guide.Category> categories,
        List<Guide.Mapping> mappings,
        List<Guide.ChecklistItem> checklist) {
}
