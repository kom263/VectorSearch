import { NavLink } from 'react-router-dom'

export default function Navbar() {
    return (
        <nav className="navbar">
            <div className="navbar-inner">
                <a href="/" className="navbar-brand">
                    <div className="navbar-logo">AI</div>
                    <span className="navbar-title">Hiring Pipeline</span>
                </a>
                <div className="navbar-links">
                    <NavLink to="/apply" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                        Apply
                    </NavLink>
                    <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                        Dashboard
                    </NavLink>
                </div>
            </div>
        </nav>
    )
}
