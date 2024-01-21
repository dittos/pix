import * as React from 'react'
import { Link, Outlet, RootRoute } from '@tanstack/react-router'
import { Route as IndexRoute } from './index'
import { addTag } from '../utils/tagQuery'

type SearchParams = {
  tag?: string
}

export const Route = new RootRoute({
  component: RootComponent,
  validateSearch: (search: Record<string, unknown>): SearchParams => ({
    tag: search?.tag as string,
  }),
  loaderDeps: ({ search }) => ({ tag: search.tag }),
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
          <div className="col-md-auto py-2 position-sticky top-0 vh-100 overflow-y-auto border-end">
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
  const search = Route.useSearch()
  return (
    <div>
      <div>
        <Link to="/" className="link-underline link-underline-opacity-50">all</Link>
      </div>
      {tags.map(tag => (
        <div key={tag.tag} className="d-flex align-items-center TagList-item">
          <Link to={IndexRoute.fullPath} search={{tag: addTag(search.tag, tag.tag)}} className="link-underline-light">
            {tag.tag}
          </Link>
          <span className="ps-2 text-secondary">{tag.image_count}</span>
          <Link to={IndexRoute.fullPath} search={{tag: addTag(search.tag, "-" + tag.tag)}} className="ms-2 link-secondary">
            not
          </Link>
          <Link to={IndexRoute.fullPath} search={{tag: tag.tag}} className="ms-1 link-secondary">
            only
          </Link>
        </div>
      ))}
    </div>
  )
}
