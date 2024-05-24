import * as React from 'react'
import { Link, LoaderFunction, useLoaderData } from 'react-router-dom'
import { useState } from 'react'
import { addTag, extractRootSearchParams, onlyTag } from '../utils/search'
import { RootLink, useExtractedSearchParams } from '../components/SearchLink'
import { useCombobox } from 'downshift'
import { useRecentlyAddedManualTags } from '../utils/manualTags'

export const imageDetailLoader: LoaderFunction = async ({ params }) => {
  return {
    image: await (await fetch(`/api/images/${encodeURIComponent(params['imageId']!)}`)).json()
  }
}

export function ImageDetailRoute({
  parentContext
}: {
  parentContext?: "searchResult"
}) {
  const {image: _image} = useLoaderData() as any
  const [image, setImage] = useState(_image)
  React.useEffect(() => setImage(_image), [_image.id])
  return (
    <DetailOverlay
      selectedImage={image}
      onClose={parentContext === "searchResult" ? () => history.back() : null}
      updateImage={setImage}
    />
  )
}

function DetailOverlay({
  selectedImage,
  onClose,
  updateImage,
}: any) {
  const isModal = !!onClose
  return (
    <>
      <div className={isModal ? "modal fade show d-flex" : "vh-fill"} style={{display: 'flex'}}>
        {isModal && (
          <div data-bs-theme="dark" className="fixed-top p-2" style={{width: '5%'}}>
            <button type="button" className="btn-close" aria-label="Close" onClick={onClose} />
          </div>
        )}
        <div className="col p-4">
          <img src={`/_images/${selectedImage.local_filename}`} style={{width: '100%', height: '100%', objectFit: 'scale-down'}} />
        </div>
        <DetailOverlaySidebar
          bsTheme={isModal ? "dark" : ""}
          selectedImage={selectedImage}
          updateImage={updateImage}
        />
      </div>
      {onClose && <div className="modal-backdrop" />}
    </>
  )
}

function DetailOverlaySidebar({
  bsTheme,
  selectedImage,
  updateImage,
}: any) {
  const [similarImages, setSimilarImages] = React.useState({
    embedding: selectedImage.embedding_types[0],
    data: [],
    isLoading: true,
  })
  const [faces, setFaces] = React.useState([])
  const [autotags, setAutotags] = React.useState([])
  const loadSimilarImages = (embedding: string) => {
    setSimilarImages({embedding, data: similarImages.data, isLoading: true})
    fetch(`/api/images/${encodeURIComponent(selectedImage.id)}/similar?embedding_type=${embedding}`)
      .then(r => r.json())
      .then(r => setSimilarImages({embedding, data: r, isLoading: false}))
  }

  React.useEffect(() => {
    if (selectedImage.embedding_types[0]) {
      loadSimilarImages(selectedImage.embedding_types[0])
    }

    fetch(`/api/images/${encodeURIComponent(selectedImage.id)}/faces`)
      .then(r => r.json())
      .then(r => setFaces(r))

    fetch(`/api/images/${encodeURIComponent(selectedImage.id)}/custom-autotags`)
      .then(r => r.json())
      .then(r => setAutotags(r))
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
    <div className="col-2 p-2 overflow-y-auto" data-bs-theme={bsTheme} style={{fontSize: '0.9rem'}}>
      {['RATING', null].map(tagType => (
        <TagList key={tagType ?? ""} tags={allTags.filter((tag: any) => tag.type === tagType)} primaryLinkClassName={bsTheme === "dark" && "link-light"} />
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
            <img src={`/_images/faces/${face.local_filename}`} style={{height: 120}} />
            <span className="ms-2">
              {face.face_cluster_label ?? face.face_cluster_id?.substring(0, 8)}
            </span>
          </div>
        )}
        <div className="d-flex flex-wrap">
          {faces.filter((face: any) => !face.face_cluster_id).map((face: any) =>
            <div className="me-2 mb-2" style={{opacity: 0.5}}>
              <img src={`/_images/faces/${face.local_filename}`} style={{height: 120}} />
            </div>
          )}
        </div>
      </>)}

      <div className="my-2 fw-bold">characters</div>
      <div className="pb-2">
        {autotags.length > 0 && (
          <div>
            ✨ {autotags.join(", ")}
          </div>
        )}
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
      <div className="my-2">
        {selectedImage.embedding_types.map((type: string) => (
          <span className="me-2">
            <a
              key={type}
              href="#"
              className={similarImages.embedding === type ? 'fw-bold' : ''}
              onClick={(e) => { e.preventDefault(); loadSimilarImages(type) }}
            >
              {type}
            </a>
          </span>
        ))}
      </div>
      <div className="d-flex flex-wrap" style={similarImages.isLoading ? {opacity: 0.5} : {}}>
        {similarImages.data.map(({image, score}: any) => (
          <div className="me-2 mb-2">
            <Link to={`/images/${image.id}`}>
              <img src={`/_images/${image.local_filename}`} style={{height: 120}} />
              <br />{score.toFixed(3)}
            </Link>
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
