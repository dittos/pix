export type QuickFilterState = undefined | "only" | "not"

export function addTag(query: string | undefined, tag: string) {
  if (!query) return tag
  const terms = query.split(" ")
  if (terms.includes(tag)) return query
  return query + " " + tag
}

export function removeTag(query: string | undefined, tag: string) {
  if (!query) return undefined
  const terms = query.split(" ").filter(term => term !== tag)
  return terms.length > 0 ? terms.join(" ") : undefined
}

export function applyQuickFilters(query: string | undefined, quickFilters: {
  sfw?: QuickFilterState
  realistic?: QuickFilterState
}) {
  query = query ?? ''
  
  if (quickFilters.sfw === "only") {
    query = "-rating:s -rating:q -rating:e " + query
  } else if (quickFilters.sfw === "not") {
    query = "-rating:g " + query
  }

  if (quickFilters.realistic === "only") {
    query = "realistic " + query
  } else if (quickFilters.realistic === "not") {
    query = "-realistic " + query
  }

  return query?.trim()
}
