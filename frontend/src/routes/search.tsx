import * as React from 'react'
import { LoaderFunction, Outlet, useLoaderData } from 'react-router-dom'
import { applyQuickFilters } from '../utils/tagQuery'
import { addTag, clearTag, extractRootSearchParams, onlyTag, setQuickFilterState } from '../utils/search'
import { RootLink, useExtractedSearchParams } from '../components/SearchLink'

export const searchLoader: LoaderFunction = async ({ request }) => {
  const url = new URL(request.url)
  const search = extractRootSearchParams(url.searchParams)
  const {tag} = search
  return {
    tags: await (await fetch("/api/tags?" + new URLSearchParams({
      q: applyQuickFilters(tag, search),
    }))).json()
  }
}

export function SearchRoute() {
  const data = useLoaderData() as any
  return (
    <>
      <div className="container-fluid">
        <div className="row">
          <div className="col-md-2 py-2 vh-fill overflow-y-auto border-end">
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

function TagList({ tags }: { tags: any[] }) {
  const [limit, setLimit] = React.useState(200)
  const search = useExtractedSearchParams(extractRootSearchParams)
  React.useEffect(() => setLimit(200), [tags])
  return (
    <div>
      <div className="mb-2 fw-bold">quick filters</div>

      <div className="mb-1 d-flex align-items-center">
        <label>sfw:</label>
        <div className="ms-2 d-inline-flex gap-1">
          <RootLink search={setQuickFilterState(search, 'sfw', undefined)} className={`btn btn-sm ${!search.sfw ? 'active' : ''}`}>any</RootLink>
          <RootLink search={setQuickFilterState(search, 'sfw', 'only')} className={`btn btn-sm ${search.sfw === 'only' ? 'active' : ''}`}>only</RootLink>
          <RootLink search={setQuickFilterState(search, 'sfw', 'not')} className={`btn btn-sm ${search.sfw === 'not' ? 'active' : ''}`}>not</RootLink>
        </div>
      </div>
      <div className="d-flex align-items-center">
        <label>realistic:</label>
        <div className="ms-2 d-inline-flex gap-1">
          <RootLink search={setQuickFilterState(search, 'realistic', undefined)} className={`btn btn-sm ${!search.realistic ? 'active' : ''}`}>any</RootLink>
          <RootLink search={setQuickFilterState(search, 'realistic', 'only')} className={`btn btn-sm ${search.realistic === 'only' ? 'active' : ''}`}>only</RootLink>
          <RootLink search={setQuickFilterState(search, 'realistic', 'not')} className={`btn btn-sm ${search.realistic === 'not' ? 'active' : ''}`}>not</RootLink>
        </div>
      </div>

      <hr />

      <div>
        <RootLink search={clearTag(search)} className="link-underline link-underline-opacity-50">all</RootLink>
      </div>
      {tags.slice(0, limit).map(tag => (
        <div key={tag.tag} className="d-flex align-items-center TagList-item">
          <RootLink search={addTag(search, tag.tag)} className="link-underline-light">
            {tag.tag}
          </RootLink>
          <span className="ps-2 text-secondary">{tag.image_count}</span>
          <RootLink search={onlyTag(search, tag.tag)} className="ms-2 link-secondary">
            only
          </RootLink>
          <RootLink search={addTag(search, "-" + tag.tag)} className="ms-1 link-secondary">
            not
          </RootLink>
        </div>
      ))}
      {tags.length > limit && (
        <div className="mb-3">
          <a href="#" className="link-secondary" onClick={(event) => { event.preventDefault(); setLimit(limit + 200) }}>
            more tags...
          </a>
        </div>
      )}
    </div>
  )
}
