import * as React from 'react'
import { LoaderFunction, useLoaderData } from 'react-router-dom'
import * as HoverCard from '@radix-ui/react-hover-card'
import { useState } from 'react'
import { applyQuickFilters } from '../utils/tagQuery'
import { addTag, extractIndexSearchParams, extractRootSearchParams, onlyTag, removeTag } from '../utils/search'
import { RootLink, useExtractedSearchParams } from '../components/SearchLink'

export const loader: LoaderFunction = async ({ request }) => {
  const url = new URL(request.url)
  const root = extractRootSearchParams(url.searchParams)
  const tag = applyQuickFilters(root.tag, root)
  const {page} = extractIndexSearchParams(url.searchParams)
  return {
    images: await (await fetch('/api/images?' + new URLSearchParams({
      ...(tag && {tag}),
      ...(page && {page: String(page)}),
    }))).json()
  }
}

export function HomeComponent() {
  const {images} = useLoaderData() as any
  const search = useExtractedSearchParams(extractRootSearchParams)
  const {page = 1} = useExtractedSearchParams(extractIndexSearchParams)
  const [selectedImage, setSelectedImage] = useState<any>()
  React.useEffect(() => {
    window.scrollTo(0, 0)
    setSelectedImage(null)
  }, [images])
  return (
    <div className="d-flex">
      <div className="col py-2">
      {search.tag && (
        <div className="my-2">
          {search.tag.split(" ").map(term => (
            <span className="border rounded p-2 me-2">{term} <RootLink search={removeTag(search, term)} className="link-underline-light">&times;</RootLink></span>
          ))}
        </div>
      )}
      <p className="mb-4">total {images.count} images</p>

      <div className="d-flex flex-wrap">
        {images.data.map((image: any) => (
          <HoverCard.HoverCard key={image.id} openDelay={0} closeDelay={0}>
            <HoverCard.HoverCardTrigger>
              <div className="me-2 mb-2">
                <div className={`rounded border overflow-hidden ${image.id === selectedImage?.id ? "image-grid-item-selected" : "image-grid-item"}`}>
                  <a href="javascript:" className="d-block"
                    onClick={() => image.id === selectedImage?.id ? setSelectedImage(null) : setSelectedImage(image)}>
                    <SmartImage src={`/images/${image.content.local_filename}`} />
                  </a>
                </div>
              </div>
            </HoverCard.HoverCardTrigger>
            <HoverCard.HoverCardContent className="HoverCardContent">
              {image.content.tags && (
                <div className="rounded bg-dark bg-opacity-75 text-white p-1 small">
                  {image.content.tags?.map((tag: any) => tag.tag).join(", ")}
                </div>
              )}
            </HoverCard.HoverCardContent>
          </HoverCard.HoverCard>
        ))}
      </div>

      <ul className="pagination justify-content-center">
        {page > 1 && (
          <li className="page-item">
            <RootLink className="page-link" search={search} indexParams={{page: page - 1}}>&larr; prev</RootLink>
          </li>
        )}
        
        {images.has_next_page && (
          <li className="page-item">
            <RootLink className="page-link" search={search} indexParams={{page: page + 1}}>next &rarr;</RootLink>
          </li>
        )}
      </ul>
      </div>

      {selectedImage && (
        <div className="col-3 border-start p-2 position-sticky top-0 vh-100 overflow-y-auto bg-body-tertiary">
          <button type="button" className="btn-close float-end" aria-label="Close" onClick={() => setSelectedImage(null)} />

          {selectedImage.content.tweet_username && (
            <p className="card-text">source: @{selectedImage.content.tweet_username}</p>
          )}
          <p className="card-text">
            {['RATING', 'CHARACTER', null].map(tagType => (
              selectedImage.content.tags?.filter((tag: any) => tag.type === tagType).map((tag: any) => (
                <div key={tag.tag} className="TagList-item">
                  <RootLink search={addTag(search, tag.tag)} className="link-underline-light">
                    {tag.tag}
                  </RootLink>
                  <span className="ps-2 text-secondary">{tag.score.toFixed(3)}</span>
                  <RootLink search={onlyTag(search, tag.tag)} className="ms-2 link-secondary">
                    only
                  </RootLink>
                  <RootLink search={addTag(search, "-" + tag.tag)} className="ms-1 link-secondary">
                    not
                  </RootLink>
                </div>
              ))
            ))}
          </p>
        </div>
      )}
    </div>
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
    // TODO: apply horizontal clip for too wide landscape image
  }
  return (
    <div className={clip ? "image-clip" : undefined} style={{overflow: 'hidden', height, maxWidth: 480}}>
      <img {...props} onLoad={onLoad} style={clip ? {width: minWidth} : {height}} />
    </div>
  )
}
