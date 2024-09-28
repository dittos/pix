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
        </div>
      </nav>

      <main style={{paddingTop: 'var(--navbar-height)'}}>
        <Outlet />
      </main>
    </>
  )
}
