import * as React from 'react'
import { Link } from 'react-router-dom'

export function SimilarImageCompare({
    queryImage,
    queryImageUrl,
    similarImages,
}: {
    queryImage?: any,
    queryImageUrl?: any,
    similarImages: any,
}) {
  const [hoveredImageId, setHoveredImageId] = React.useState<string | null>(null)
  return (
    <div>
      <div className="d-flex flex-nowrap align-items-center py-2 bg-secondary-subtle">
        <p className="col-1 text-end fw-bold me-3">query</p>
        {queryImage ? (
            <Link to={`/images/${queryImage.id}`}>
                <img src={`/_images/${queryImage.local_filename}`} style={{height: 130}} />
            </Link>
        ) : (
            <img src={queryImageUrl} style={{height: 130}} />
        )}
      </div>
      {similarImages.map(({type, images}: any) => (
        <div key={type} className="d-flex flex-nowrap align-items-center py-1 border-top">
          <p className="col-1 text-end me-3">{type}</p>
          {images.map(({image, score}: any, index: number) => (
            <div className="me-2" key={type + image.id}>
              <Link
                to={`/images/${image.id}/similar`}
                className="fs-6"
                onMouseOver={() => setHoveredImageId(image.id)}
                onMouseOut={() => setHoveredImageId(null)}
              >
                <img src={`/_images/${image.local_filename}`} style={{height: 130, boxShadow: hoveredImageId === image.id ? '0 0 10px blue' : undefined}} />
              </Link>
              <div style={{fontSize: '0.8rem'}} className={index === 0 ? 'fw-bold text-primary' : ''}>
                {score.toFixed(3)}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
