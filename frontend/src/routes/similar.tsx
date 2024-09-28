import { useState } from "react";
import { LoaderFunction, useLoaderData, useSearchParams } from "react-router-dom";
import { SimilarImageCompare } from "../components/SimilarImageCompare";

export const similarLoader: LoaderFunction = async ({ request }) => {
  const searchParams = new URL(request.url).searchParams
  const queryImageUrl = searchParams.get('url')
  if (queryImageUrl) {
    const similarImages = await fetch(`/api/images/search/similar/compare?url=${encodeURIComponent(queryImageUrl)}`)
      .then(r => r.json())
    similarImages.sort((a: any, b: any) => a.type === "default" ? a : a.type.localeCompare(b.type))
    return {
      queryImageUrl,
      similarImages,
    }
  }
  return {}
}

export function SimilarRoute() {
  const {queryImageUrl = '', similarImages = []} = useLoaderData() as any
  const [inputUrl, setInputUrl] = useState('');
  const [_, setSearchParams] = useSearchParams();

  const search = () => {
    setSearchParams({url: inputUrl});
  };

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="my-2">
          <input type="text" placeholder="Enter Image URL..." size={50} value={inputUrl} onChange={e => setInputUrl(e.target.value)} />
          <button type="button" onClick={search}>Search</button>
        </div>
      </div>
      <SimilarImageCompare
        queryImageUrl={queryImageUrl}
        similarImages={similarImages}
      />
    </div>
  );
}
