import { Link, useSearchParams, createSearchParams } from 'react-router-dom'
import { IndexSearchParams, RootSearchParams } from "../utils/search"

export const RootLink: React.FC<React.PropsWithChildren<{
  search: RootSearchParams,
  indexParams?: IndexSearchParams,
}> & React.HTMLAttributes<HTMLAnchorElement>> = ({
  search,
  indexParams,
  ...props
}) => {
  const searchParams = createSearchParams()
  for (const [key, value] of Object.entries(search)) {
    if (value != null)
      searchParams.set(key, value.toString())
  }
  if (indexParams) {
    for (const [key, value] of Object.entries(indexParams)) {
      if (value != null)
        searchParams.set(key, value.toString())
    }
  }
  return (
    <Link to={{pathname: '/search', search: searchParams.toString()}} {...props} />
  )
}

export function useExtractedSearchParams<T>(extractor: (searchParams: URLSearchParams) => T): T {
  const [searchParams] = useSearchParams()
  return extractor(searchParams)
}
