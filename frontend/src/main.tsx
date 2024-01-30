import React from 'react'
import ReactDOM from 'react-dom/client'
import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom"
import './style.css'
import 'bootstrap/dist/css/bootstrap.css'
import { loader, RootComponent } from './routes/__root'
import { HomeComponent, loader as homeLoader } from './routes'
import { extractRootSearchParams } from './utils/search'
import isEqual from 'lodash/isEqual'

const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/search" />,
  },
  {
    path: "/search",
    element: <RootComponent />,
    loader,
    shouldRevalidate: ({ currentUrl, nextUrl }) => {
      return !isEqual(extractRootSearchParams(currentUrl.searchParams), extractRootSearchParams(nextUrl.searchParams))
    },
    children: [
      {
        index: true,
        element: <HomeComponent />,
        loader: homeLoader
      }
    ]
  },
])

const rootElement = document.getElementById('root')!

if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(<RouterProvider router={router} />)
}
