import * as TagQuery from "./tagQuery"

type Search = {
  tag?: string
  sfw?: TagQuery.QuickFilterState
  realistic?: TagQuery.QuickFilterState
  page?: number
}

export function addTagReducer(tag: string) {
  return (search: Search) => ({
    ...search,
    tag: TagQuery.addTag(search.tag, tag),
    page: undefined, // reset
  })
}

export function removeTagReducer(tag: string) {
  return (search: Search) => ({
    ...search,
    tag: TagQuery.removeTag(search.tag, tag),
    page: undefined, // reset
  })
}

export function onlyTagReducer(tag: string) {
  return (search: Search) => ({
    ...search,
    tag,
    page: undefined, // reset
  })
}

export function clearTagReducer() {
  return (search: Search) => ({
    ...search,
    tag: undefined, // reset
    page: undefined, // reset
  })
}

export function setQuickFilterStateReducer(key: 'sfw' | 'realistic', state: TagQuery.QuickFilterState) {
  return (search: Search) => ({
    ...search,
    [key]: state,
    page: undefined, // reset
  })
}
