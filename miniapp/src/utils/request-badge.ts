type RequestBadgeInput = {
  code?: string | null;
  category?: string | null;
};

const CATEGORY_BADGES: Record<string, string> = {
  LEAVE: "假",
  CERTIFICATE: "证",
  STAMP: "章",
  REGISTRATION: "报",
  MATERIAL: "材",
  OTHER: "事",
};

export function getRequestCategoryBadge(category?: string | null) {
  const normalized = (category || "").toUpperCase();
  return CATEGORY_BADGES[normalized] || "事";
}

export function getRequestTypeBadge(
  input?: string | null | RequestBadgeInput,
  fallbackCategory?: string | null,
) {
  const code = typeof input === "object" ? input?.code : input;
  const category = typeof input === "object" ? input?.category : fallbackCategory;
  const normalizedCategory = (category || "").toUpperCase();
  if (normalizedCategory && normalizedCategory !== "OTHER") {
    return getRequestCategoryBadge(normalizedCategory);
  }

  const normalizedCode = (code || "").toUpperCase();
  if (normalizedCode.includes("CERT")) return "证";
  if (normalizedCode.includes("LEAVE") || normalizedCode.includes("SICK")) return "假";
  if (normalizedCode.includes("STAMP") || normalizedCode.includes("SEAL")) return "章";
  if (
    normalizedCode.includes("REGISTRATION") ||
    normalizedCode.includes("REG_") ||
    normalizedCode.includes("ACTIVITY") ||
    normalizedCode.includes("EVENT")
  ) {
    return "报";
  }
  if (normalizedCode.includes("MATERIAL") || normalizedCode.includes("DOCUMENT")) return "材";
  if (normalizedCode.includes("GRADE") || normalizedCode.includes("SCORE")) return "绩";
  if (normalizedCode.includes("SCHOLAR") || normalizedCode.includes("HONOR")) return "奖";
  return "事";
}
