import * as React from 'react'
import { Link, LoaderFunction, Outlet, useLoaderData, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { applyQuickFilters } from '../utils/tagQuery'
import { extractIndexSearchParams, extractRootSearchParams, removeTag, setSort } from '../utils/search'
import { RootLink, useExtractedSearchParams } from '../components/SearchLink'

export const searchResultLoader: LoaderFunction = async ({ request }) => {
  const url = new URL(request.url)
  const root = extractRootSearchParams(url.searchParams)
  const tag = applyQuickFilters(root.tag, root)
  const {page} = extractIndexSearchParams(url.searchParams)
  return {
    images: await (await fetch('/api/images?' + new URLSearchParams({
      ...(tag && {tag}),
      ...(page && {page: String(page)}),
      ...(root.sort && {sort: root.sort}),
    }))).json()
  }
}

export function SearchResultRoute() {
  const {images} = useLoaderData() as any
  const search = useExtractedSearchParams(extractRootSearchParams)
  const {page = 1} = useExtractedSearchParams(extractIndexSearchParams)
  const location = useLocation()
  React.useEffect(() => {
    window.scrollTo(0, 0)
  }, [images])
  const imageList = images.data

  const queryTerms = []
  if (search.tag) {
    for (const term of search.tag.split(" ")) {
      let label = term
      const faceCluster = images.query_face_clusters.find((it: any) => it.raw_term === term)
      if (faceCluster) {
        if (faceCluster.label) {
          label = faceCluster.label
        } else {
          label = `face:${faceCluster.id.substring(0, 8)}`
        }
        if (term[0] == '-') {
          label = '-' + label
        }
      }
      queryTerms.push(
        <span className="border rounded p-2 me-2">{label} <RootLink search={removeTag(search, term)} className="link-underline-light">&times;</RootLink></span>
      )
    }
  }

  return (
    <div className="d-flex">
      <div className="col py-2">
      {queryTerms.length > 0 && (
        <div className="my-2">
          {queryTerms}
        </div>
      )}

      <p className="mb-4">
        total {images.count} images
        / sort by date:{' '}
        <RootLink search={setSort(search, 'desc')} className={search.sort === 'desc' ? 'fw-bold' : ''}>desc</RootLink>{' '}
        <RootLink search={setSort(search, 'asc')} className={search.sort === 'asc' ? 'fw-bold' : ''}>asc</RootLink>
      </p>

      <div className="d-flex flex-wrap">
        {imageList.map((image: any) => (
          <div className="me-2 mb-2">
            <div className={`rounded border overflow-hidden image-grid-item`}>
              <Link to={{pathname: `images/${encodeURIComponent(image.id)}`, search: location.search}} className="d-block">
                <SmartImage src={`/_images/${image.local_filename}`} />
              </Link>
            </div>
          </div>
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

      <Outlet />
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
      <img key={props.src} {...props} onLoad={onLoad} style={clip ? {width: minWidth} : {height}} />
    </div>
  )
}
