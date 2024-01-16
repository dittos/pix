import * as React from 'react'
import { FileRoute, Link } from '@tanstack/react-router'
import * as HoverCard from '@radix-ui/react-hover-card'
import { useState } from 'react'

export const Route = new FileRoute('/').createRoute({
  component: HomeComponent,
  loaderDeps: ({ search }) => ({ tag: search.tag, page: search.page }),
  loader: async ({ deps: { tag, page } }) => ({
    images: await (await fetch('/api/images?' + new URLSearchParams({
      ...(tag && {tag}),
      ...(page && {page}),
    }))).json()
  })
})

function HomeComponent() {
  const {images} = Route.useLoaderData()
  const search = Route.useSearch()
  React.useEffect(() => {
    window.scrollTo(0, 0)
  }, [images])
  return (
    <>
      {search.tag && <h2>{search.tag}</h2>}
      <p className="mb-4">total {images.count} images</p>

      <div className="d-flex flex-wrap">
        {images.data.map((image: any) => (
          <div className="me-2 mb-2" key={image.id}>
            <HoverCard.Root openDelay={0} closeDelay={0}>
              <HoverCard.Trigger>
                <div className="image-grid-item">
                  <a href="javascript:" className="d-block">
                    <SmartImage src={image.content.source_url} loading="lazy" />
                  </a>
                </div>
              </HoverCard.Trigger>
              <HoverCard.Portal>
                <HoverCard.Content collisionPadding={10}>
                  <div className="card overflow-auto HoverCardContent shadow-lg w-100">
                    <div className="card-body">
                      {image.content.tweet_username && (
                        <p className="card-text">source: @{image.content.tweet_username}</p>
                      )}
                      <p className="card-text">
                        {image.content.tags?.map((tag: any) => (<div>
                          <Link to="/" search={{tag: tag.tag}}>{tag.tag}</Link> {tag.score.toFixed(3)}<br />
                          </div>))}
                      </p>
                    </div>
                  </div>
                </HoverCard.Content>
              </HoverCard.Portal>
            </HoverCard.Root>
          </div>
        ))}
      </div>

      <ul className="pagination justify-content-center">
        {search.page > 1 && (
          <li className="page-item">
            <Link className="page-link" to="/" search={{...search, page: (search.page || 1) - 1}}>&larr; prev</Link>
          </li>
        )}
        
        {images.has_next_page && (
          <li className="page-item">
            <Link className="page-link" to="/" search={{...search, page: (search.page || 1) + 1}}>next &rarr;</Link>
          </li>
        )}
      </ul>
    </>
  )
}

function SmartImage(props: any) {
  const [size, setSize] = useState<[number, number]>()
  const onLoad: React.ReactEventHandler<HTMLImageElement> = (event) => {
    const el = event.target as HTMLImageElement
    setSize([el.naturalWidth, el.naturalHeight])
  }
  let height = 240
  const minWidth = height / 2
  let clip = false
  if (size) {
    const resizedWidth = height / size[1] * size[0]
    if (resizedWidth < minWidth) {
      clip = true
    }
  }
  return (
    <div className={clip ? "image-clip" : undefined} style={{height}}>
      <img {...props} onLoad={onLoad} style={clip ? {width: minWidth} : {height}} />
    </div>
  )
}
