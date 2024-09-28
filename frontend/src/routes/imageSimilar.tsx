import * as React from 'react'
import { LoaderFunction, useLoaderData } from 'react-router-dom'
import { SimilarImageCompare } from '../components/SimilarImageCompare'

export const imageSimilarLoader: LoaderFunction = async ({ params }) => {
  const queryImage = await (await fetch(`/api/images/${encodeURIComponent(params['imageId']!)}`)).json()
  const similarImages = await fetch(`/api/images/${encodeURIComponent(queryImage.id)}/similar/compare`)
      .then(r => r.json())
  similarImages.sort((a: any, b: any) => a.type === "default" ? a : a.type.localeCompare(b.type))
  return {
    queryImage,
    similarImages,
  }
}

export function ImageSimilarRoute() {
  const {queryImage, similarImages} = useLoaderData() as any
  return (
    <SimilarImageCompare
      queryImage={queryImage}
      similarImages={similarImages}
    />
  );
}
