import * as TagQuery from "./tagQuery"

export type RootSearchParams = {
  tag?: string
  sfw?: TagQuery.QuickFilterState
  realistic?: TagQuery.QuickFilterState
  sort?: 'asc' | 'desc'
}

export function extractRootSearchParams(searchParams: URLSearchParams): RootSearchParams {
  const sortParam = searchParams.get('sort')
  return {
    tag: searchParams.get('tag') ?? undefined,
    sfw: searchParams.get('sfw') as TagQuery.QuickFilterState,
    realistic: searchParams.get('realistic') as TagQuery.QuickFilterState,
    sort: sortParam === 'asc' || sortParam === 'desc' ? sortParam : 'desc',
  }
}

export type IndexSearchParams = {
  page?: number
}

export function extractIndexSearchParams(searchParams: URLSearchParams): IndexSearchParams {
  const pageParam = searchParams.get('page')
  return {
    page: pageParam ? Number(pageParam) : 1,
  }
}

export function addTag(search: RootSearchParams, tag: string): RootSearchParams {
  return {
    ...search,
    tag: TagQuery.addTag(search.tag, tag),
  }
}

export function removeTag(search: RootSearchParams, tag: string): RootSearchParams {
  return {
    ...search,
    tag: TagQuery.removeTag(search.tag, tag),
  }
}

export function onlyTag(search: RootSearchParams, tag: string): RootSearchParams {
  return {
    ...search,
    tag,
  }
}

export function clearTag(search: RootSearchParams): RootSearchParams {
  return {
    ...search,
    tag: undefined, // reset
  }
}

export function setQuickFilterState(search: RootSearchParams, key: 'sfw' | 'realistic', state: TagQuery.QuickFilterState): RootSearchParams {
  return {
    ...search,
    [key]: state,
  }
}

export function setSort(search: RootSearchParams, sort: 'asc' | 'desc'): RootSearchParams {
  return {
    ...search,
    sort,
  }
}
