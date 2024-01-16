import * as React from 'react'
import { Link, Outlet, RootRoute } from '@tanstack/react-router'

export const Route = new RootRoute({
  component: RootComponent,
  loader: async () => ({
    tags: await (await fetch("/api/tags")).json()
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
          <div className="col py-2">
            <Outlet />
          </div>
        </div>
      </div>
    </>
  )
}

function TagList({ tags }: { tags: any[] }) {
  return (
    <div>
      <div>
        <Link to="/" className="link-underline link-underline-opacity-50">all</Link>
      </div>
      {tags.map(tag => (
        <div key={tag.tag}>
          <Link to="/" search={{tag: tag.tag}} className="link-underline link-underline-opacity-50">
            {tag.tag}
          </Link>
          <span className="ps-2 text-secondary">{tag.image_count}</span>
        </div>
      ))}
    </div>
  )
}
