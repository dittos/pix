import * as React from 'react'
import { LoaderFunction, useLoaderData } from 'react-router-dom'
import { useState } from 'react'
import { applyQuickFilters } from '../utils/tagQuery'
import { addTag, extractIndexSearchParams, extractRootSearchParams, onlyTag, removeTag } from '../utils/search'
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
    }))).json()
  }
}

export function SearchResultRoute() {
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
          <div className="me-2 mb-2">
            <div className={`rounded border overflow-hidden ${image.id === selectedImage?.id ? "image-grid-item-selected" : "image-grid-item"}`}>
              <a href="javascript:" className="d-block"
                onClick={() => image.id === selectedImage?.id ? setSelectedImage(null) : setSelectedImage(image)}>
                <SmartImage src={`/images/${image.local_filename}`} />
              </a>
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

      {selectedImage && (
        <DetailPanel
          key={selectedImage.id}
          selectedImage={selectedImage}
          onClose={() => setSelectedImage(null)}
        />
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
      <img key={props.src} {...props} onLoad={onLoad} style={clip ? {width: minWidth} : {height}} />
    </div>
  )
}

function DetailPanel({
  selectedImage,
  onClose,
}: any) {
  const search = useExtractedSearchParams(extractRootSearchParams)
  const [similarImages, setSimilarImages] = React.useState([])
  const [faces, setFaces] = React.useState([])
  React.useEffect(() => {
    fetch(`/api/images/${encodeURIComponent(selectedImage.id)}/similar`)
      .then(r => r.json())
      .then(r => setSimilarImages(r))

    fetch(`/api/images/${encodeURIComponent(selectedImage.id)}/faces`)
      .then(r => r.json())
      .then(r => setFaces(r))
  }, [selectedImage.id])

  return (
    <div className="col-3 border-start p-2 vh-fill overflow-y-auto bg-body-tertiary">
      <button type="button" className="btn-close float-end" aria-label="Close" onClick={onClose} />

      {selectedImage.tweet_username && (
        <p className="card-text">source: @{selectedImage.tweet_username}</p>
      )}

      {(faces?.length ?? 0) > 0 && (<>
        <div className="mb-2 fw-bold">faces</div>
        {faces.filter((face: any) => face.face_cluster_id).map((face: any) =>
          <div className="me-2 mb-2">
            <img src={`/images/faces/${face.local_filename}`} style={{height: 120}} />
            <span className="ms-2">
              {face.face_cluster_label ?? face.face_cluster_id?.substring(0, 8)}
            </span>
          </div>
        )}
        <div className="d-flex flex-wrap">
          {faces.filter((face: any) => !face.face_cluster_id).map((face: any) =>
            <div className="me-2 mb-2" style={{opacity: 0.5}}>
              <img src={`/images/faces/${face.local_filename}`} style={{height: 120}} />
            </div>
          )}
        </div>
      </>)}

      <div className="my-2 fw-bold">similar</div>
      <div className="d-flex flex-wrap">
        {similarImages.map(({image, score}: any) => (
          <div className="me-2 mb-2">
            <img src={`/images/${image.local_filename}`} style={{height: 120}} />
            <br />{score.toFixed(3)}
          </div>
        ))}
      </div>

      <div className="my-2 fw-bold">tags</div>
      {['RATING', 'CHARACTER', null].map(tagType => (
        selectedImage.tags?.filter((tag: any) => tag.type === tagType).map((tag: any) => (
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
    </div>
  )
}