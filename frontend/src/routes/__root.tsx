import * as React from 'react'
import { Link, Outlet, RootRoute } from '@tanstack/react-router'
import { QuickFilterState, applyQuickFilters } from '../utils/tagQuery'
import { addTagReducer, clearTagReducer, onlyTagReducer, setQuickFilterStateReducer } from '../utils/search'

type SearchParams = {
  tag?: string
  sfw?: QuickFilterState
  realistic?: QuickFilterState
}

export const Route = new RootRoute({
  component: RootComponent,
  validateSearch: (search: Record<string, unknown>): SearchParams => ({
    tag: search?.tag as string,
    sfw: search?.sfw as QuickFilterState,
    realistic: search?.realistic as QuickFilterState,
  }),
  loaderDeps: ({ search }) => ({ tag: applyQuickFilters(search.tag, search) }),
  loader: async ({ deps: { tag } }) => ({
    tags: await (await fetch("/api/tags?" + new URLSearchParams({
      ...(tag && {q: tag}),
    }))).json()
  })
})

function RootComponent() {
  const data = Route.useLoaderData()
  return (
    <>
      <div className="container-fluid">
        <div className="row">
          <div className="col-md-2 py-2 position-sticky top-0 vh-100 overflow-y-auto border-end">
            <TagList tags={data.tags} />
          </div>
          <div className="col">
            <Outlet />
          </div>
        </div>
      </div>
    </>
  )
}

function QuickFilters() {
  const search = Route.useSearch()
  return (
    <div>
      <div className="mb-2 fw-bold">quick filters</div>

      <div className="mb-1 d-flex align-items-center">
        <label>sfw:</label>
        <div className="ms-2 d-inline-flex gap-1">
          <Link to="/" search={setQuickFilterStateReducer('sfw', undefined)} className={`btn btn-sm ${!search.sfw ? 'active' : ''}`}>any</Link>
          <Link to="/" search={setQuickFilterStateReducer('sfw', 'only')} className={`btn btn-sm ${search.sfw === 'only' ? 'active' : ''}`}>only</Link>
          <Link to="/" search={setQuickFilterStateReducer('sfw', 'not')} className={`btn btn-sm ${search.sfw === 'not' ? 'active' : ''}`}>not</Link>
        </div>
      </div>
      <div className="d-flex align-items-center">
        <label>realistic:</label>
        <div className="ms-2 d-inline-flex gap-1">
          <Link to="/" search={setQuickFilterStateReducer('realistic', undefined)} className={`btn btn-sm ${!search.realistic ? 'active' : ''}`}>any</Link>
          <Link to="/" search={setQuickFilterStateReducer('realistic', 'only')} className={`btn btn-sm ${search.realistic === 'only' ? 'active' : ''}`}>only</Link>
          <Link to="/" search={setQuickFilterStateReducer('realistic', 'not')} className={`btn btn-sm ${search.realistic === 'not' ? 'active' : ''}`}>not</Link>
        </div>
      </div>
    </div>
  )
}

function TagList({ tags }: { tags: any[] }) {
  return (
    <div>
      <QuickFilters />
      <hr />
      <div>
        <Link to="/" search={clearTagReducer()} className="link-underline link-underline-opacity-50">all</Link>
      </div>
      {tags.slice(0, 100).map(tag => (
        <div key={tag.tag} className="d-flex align-items-center TagList-item">
          <Link to="/" search={addTagReducer(tag.tag)} className="link-underline-light">
            {tag.tag}
          </Link>
          <span className="ps-2 text-secondary">{tag.image_count}</span>
          <Link to="/" search={onlyTagReducer(tag.tag)} className="ms-2 link-secondary">
            only
          </Link>
          <Link to="/" search={addTagReducer("-" + tag.tag)} className="ms-1 link-secondary">
            not
          </Link>
        </div>
      ))}
    </div>
  )
}
