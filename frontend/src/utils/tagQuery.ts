export function addTag(query: string | undefined, tag: string) {
  if (!query) return tag
  const terms = query.split(" ")
  if (terms.includes(tag)) return query
  return query + " " + tag
}

export function removeTag(query: string | undefined, tag: string) {
  if (!query) return undefined
  return query.split(" ").filter(term => term !== tag).join(" ")
}
