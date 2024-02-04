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
            index: true,
            element: <SearchResultRoute />,
            loader: searchResultLoader,
          }
        ]
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
