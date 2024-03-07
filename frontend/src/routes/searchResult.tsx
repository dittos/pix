import * as React from 'react'
import { LoaderFunction, useLoaderData } from 'react-router-dom'
import { useState } from 'react'
import { applyQuickFilters } from '../utils/tagQuery'
import { addTag, extractIndexSearchParams, extractRootSearchParams, onlyTag, removeTag } from '../utils/search'
import { RootLink, useExtractedSearchParams } from '../components/SearchLink'
import { useCombobox } from 'downshift'
import { useListUpdater } from '../utils/listUpdater'
import { useRecentlyAddedManualTags } from '../utils/manualTags'

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
  const [imageList, updateImageInList] = useListUpdater<any>(images.data, obj => obj.id)
  const updateImage = (image: any) => {
    updateImageInList(image)
    if (selectedImage?.id === image.id) {
      setSelectedImage(image)
    }
  }

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
        {imageList.map((image: any) => (
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
        <DetailOverlay
          key={selectedImage.id}
          selectedImage={selectedImage}
          onClose={() => setSelectedImage(null)}
          updateImage={updateImage}
        />
      )}
    </div>
  )
}

function DetailOverlay({
  selectedImage,
  onClose,
  updateImage,
}: any) {
  return (
    <>
      <div className="modal fade show d-flex" style={{display: 'block'}}>
        <div data-bs-theme="dark" className="fixed-top p-2" style={{width: '5%'}}>
          <button type="button" className="btn-close" aria-label="Close" onClick={onClose} />
        </div>
        <div className="col p-4">
          <img src={`/images/${selectedImage.local_filename}`} style={{width: '100%', height: '100%', objectFit: 'scale-down'}} />
        </div>
        <DetailOverlaySidebar
          selectedImage={selectedImage}
          updateImage={updateImage}
        />
      </div>
      <div className="modal-backdrop" />
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
    // TODO: apply horizontal clip for too wide landscape image
  }
  return (
    <div className={clip ? "image-clip" : undefined} style={{overflow: 'hidden', height, maxWidth: 480}}>
      <img key={props.src} {...props} onLoad={onLoad} style={clip ? {width: minWidth} : {height}} />
    </div>
  )
}

function DetailOverlaySidebar({
  selectedImage,
  updateImage,
}: any) {
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

  const allTags = (selectedImage.manual_tags?.map((it: any) => ({...it, is_manual: true})) ?? []).concat(selectedImage.tags ?? [])

  const [recentTags, addRecentTag] = useRecentlyAddedManualTags()
  const addCharacterTag = (name: string) => {
    const manualTags = selectedImage.manual_tags?.slice() ?? []
    manualTags.push({
      tag: name,
      type: 'CHARACTER',
    })
    fetch(`/api/images/${selectedImage.id}/manual-tags`, {
      method: 'PUT',
      body: JSON.stringify({manual_tags: manualTags}),
      headers: {'Content-Type': 'application/json'},
    }).then(r => {
      if (r.ok) return r.json()
      else return r.json().then(e => { throw new Error(e.detail) })
    }).then(r => {
      updateImage(r)
    }).catch(e => alert(e.message))

    addRecentTag(name)
  }
  const removeCharacterTag = (name: string) => {
    const manualTags = selectedImage.manual_tags?.filter((tag: any) => tag.tag !== name) ?? []
    fetch(`/api/images/${selectedImage.id}/manual-tags`, {
      method: 'PUT',
      body: JSON.stringify({manual_tags: manualTags}),
      headers: {'Content-Type': 'application/json'},
    }).then(r => {
      if (r.ok) return r.json()
      else return r.json().then(e => { throw new Error(e.detail) })
    }).then(r => {
      updateImage(r)
    }).catch(e => alert(e.message))
  }

  return (<>
    <div className="col-2 p-2 overflow-y-auto" data-bs-theme="dark" style={{fontSize: '0.9rem'}}>
      {['RATING', null].map(tagType => (
        <TagList key={tagType ?? ""} tags={allTags.filter((tag: any) => tag.type === tagType)} primaryLinkClassName="link-light" />
      ))}
    </div>
    <div className="col-3 border-start p-2 overflow-y-auto bg-body-tertiary">
      {selectedImage.tweet_id && selectedImage.tweet_username && (
        <p className="card-text">source: <a href={`https://twitter.com/_/status/${selectedImage.tweet_id}`} target="_blank">@{selectedImage.tweet_username}</a></p>
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

      <div className="my-2 fw-bold">characters</div>
      <div className="pb-2">
        <TagList
          tags={allTags.filter((tag: any) => tag.type === 'CHARACTER')}
          onRemove={(tag: any) => removeCharacterTag(tag)}
        />
        <CharacterSelector onSelect={addCharacterTag} />
        recently added: {recentTags.map(tag => (
          <button key={tag} type="button" onClick={() => addCharacterTag(tag)}>+ {tag}</button>
        ))}
      </div>

      <div className="my-2 fw-bold">similar</div>
      <div className="d-flex flex-wrap">
        {similarImages.map(({image, score}: any) => (
          <div className="me-2 mb-2">
            <img src={`/images/${image.local_filename}`} style={{height: 120}} />
            <br />{score.toFixed(3)}
          </div>
        ))}
      </div>
      </div>
    </>
  )
}

function TagList({ tags, onRemove, primaryLinkClassName }: any) {
  const search = useExtractedSearchParams(extractRootSearchParams)
  return tags.map((tag: any) => (
    <div key={tag.tag} className="TagList-item">
      {tag.is_manual && onRemove && <a href="#" onClick={e => { e.preventDefault(); onRemove(tag.tag) }} className="link-danger me-1">X</a>}
      <RootLink search={addTag(search, tag.tag)} className={primaryLinkClassName}>
        {tag.tag}
      </RootLink>
      <span className="ps-2 text-secondary">{tag.score ? tag.score.toFixed(3) : ''}</span>
      <RootLink search={onlyTag(search, tag.tag)} className="ms-2 link-secondary">
        only
      </RootLink>
      <RootLink search={addTag(search, "-" + tag.tag)} className="ms-1 link-secondary">
        not
      </RootLink>
    </div>
  ))
}

function CharacterSelector({
  onSelect
}: any) {
  const [items, setItems] = useState<any[]>([])
  const {
    isOpen,
    getMenuProps,
    getInputProps,
    highlightedIndex,
    getItemProps,
    selectedItem,
    reset,
  } = useCombobox({
    onInputValueChange({inputValue}) {
      if (inputValue) {
        fetch('/api/tags/character?' + new URLSearchParams({q: inputValue}))
          .then(r => r.json())
          .then(r => setItems(r))
      } else {
        setItems([])
      }
    },
    onSelectedItemChange({selectedItem}) {
      if (selectedItem) {
        onSelect(selectedItem.name)
      }
      reset()
    },
    items,
    itemToString(item) {
      return item ? item.name : ''
    },
  })

  return (
    <div>
      <div className="w-72 d-flex flex-column gap-1">
        <div className="d-flex">
          <input
            placeholder="Add tag"
            className="w-full p-1.5"
            {...getInputProps()}
          />
        </div>
      </div>
      <ul
        className={`position-absolute w-72 bg-white mt-1 shadow overflow-scroll p-0 z-10 ${
          !(isOpen && items.length) && 'hidden'
        }`}
        style={{maxHeight: 300}}
        {...getMenuProps()}
      >
        {isOpen &&
          items.map((item, index) => (
            <li
              className={`
                ${highlightedIndex === index ? 'bg-secondary-subtle' : ''}
                ${selectedItem === item ? 'font-bold' : ''}
                py-2 px-3 d-flex flex-col
              `}
              key={item.id}
              {...getItemProps({item, index})}
            >
              <span>{item.name}</span>
              <span className="ps-3 text-secondary">{item.danbooru_post_count}</span>
            </li>
          ))}
      </ul>
    </div>
  )
}
