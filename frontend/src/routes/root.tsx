import React, { useEffect, useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";

export function RootRoute() {
  return (
    <>
      <nav className="navbar navbar-expand-lg bg-body-tertiary fixed-top" data-bs-theme="dark">
        <div className="container-fluid">
          <Link to="/" className="navbar-brand">pix</Link>

          <ul className="navbar-nav me-auto mb-2 mb-lg-0">
            <li className="nav-item">
              <NavLink to="/search" className="nav-link">Tags</NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/similar" className="nav-link">Similar</NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/faces" className="nav-link">Faces</NavLink>
            </li>
          </ul>

          <div className="navbar-text">
            <PipelineStatus />
          </div>
        </div>
      </nav>

      <main style={{paddingTop: 'var(--navbar-height)'}}>
        <Outlet />
      </main>
    </>
  )
}

function PipelineStatus() {
  const {status, run} = usePipelineStatus()

  return <span>
    Last update: {status?.last_updated ? new Date(status.last_updated).toLocaleTimeString() : 'N/A'}
    {' '}
    {status.is_running ? (
      '(Running...)'
    ) : (
      <a href="#" onClick={run}>Run now</a>
    )}
  </span>
}

function usePipelineStatus() {
  type Status = {
    is_running: boolean,
    last_updated: string | null,
  }

  const [status, setStatus] = useState<Status>({
    is_running: false,
    last_updated: null,
  })

  const reload = () => {
    fetch(`/api/tasks/pipeline/status`)
      .then(r => r.json())
      .then(r => updateStatus(r))
  }

  const updateStatus = (r: Status) => {
    setStatus(r)

    const delaySeconds = r.is_running ? 5 : 60
    setTimeout(reload, delaySeconds * 1000)
  }

  useEffect(() => {
    reload()
  }, [])

  const run = (event: React.MouseEvent) => {
    event.preventDefault()
    fetch(`/api/tasks/pipeline/execute`, {method: 'POST'})
      .then(r => r.json())
      .then(r => updateStatus(r))
  }

  return {status, run}
}
