import React from 'react'
import ReactDOM from 'react-dom/client'
import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom"
import './style.css'
import 'bootstrap/dist/css/bootstrap.css'
import { SearchRoute, searchLoader } from './routes/search'
import { SearchResultRoute, searchResultLoader } from './routes/searchResult'
import { FacesRoute, facesLoader } from './routes/faces'
import { extractRootSearchParams } from './utils/search'
import isEqual from 'lodash/isEqual'
import { RootRoute } from './routes/root'
import { imageDetailLoader, ImageDetailRoute } from './routes/imageDetail'

const router = createBrowserRouter([
  {
    path: "/",
    element: <RootRoute />,
    children: [
      {
        path: "",
        element: <Navigate to="/search" />,
      },
      {
        path: "search",
        element: <SearchRoute />,
        loader: searchLoader,
        shouldRevalidate: ({ currentUrl, nextUrl }) => {
          return !isEqual(extractRootSearchParams(currentUrl.searchParams), extractRootSearchParams(nextUrl.searchParams))
        },
        children: [
          {
            path: "",
            element: <SearchResultRoute />,
            loader: searchResultLoader,
            children: [
              {
                path: "images/:imageId",
                element: <ImageDetailRoute parentContext="searchResult" />,
                loader: imageDetailLoader,
              }
            ]
          }
        ]
      },
      {
        path: "i/:imageId",
        element: <ImageDetailRoute />,
        loader: imageDetailLoader,
      },
      {
        path: "faces",
        element: <FacesRoute />,
        loader: facesLoader,
      },
    ],
  }
])

const rootElement = document.getElementById('root')!

if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(<RouterProvider router={router} />)
}
