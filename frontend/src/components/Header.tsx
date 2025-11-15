import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { isAdmin, isCoach, isClient } from '../types/user';
import './Header.css';

export default function Header() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setIsMobileMenuOpen(false);
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'es' : 'en';
    i18n.changeLanguage(newLang);
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  const renderNavLinks = () => {
    if (isAdmin(user)) {
      return (
        <>
          <Link to="/dashboard" className="nav-link">{t('nav.dashboard')}</Link>
          <Link to="/users" className="nav-link">Users</Link>
          <Link to="/subscriptions" className="nav-link">Subscriptions</Link>
          <Link to="/locations" className="nav-link">Locations</Link>
        </>
      );
    } else if (isCoach(user)) {
      return (
        <>
          <Link to="/dashboard" className="nav-link">{t('nav.dashboard')}</Link>
          <Link to="/clients" className="nav-link">{t('nav.clients')}</Link>
          <Link to="/programs" className="nav-link">{t('nav.programs')}</Link>
          <Link to="/program-builder" className="nav-link">{t('nav.programBuilder')}</Link>
        </>
      );
    } else if (isClient(user)) {
      return (
        <>
          <Link to="/dashboard" className="nav-link">{t('nav.dashboard')}</Link>
          <Link to="/my-programs" className="nav-link">My Programs</Link>
          <Link to="/progress" className="nav-link">Progress</Link>
        </>
      );
    }
    return null;
  };

  const renderMobileNavLinks = () => {
    if (isAdmin(user)) {
      return (
        <>
          <Link to="/dashboard" className="mobile-nav-link" onClick={closeMobileMenu}>
            {t('nav.dashboard')}
          </Link>
          <Link to="/users" className="mobile-nav-link" onClick={closeMobileMenu}>
            Users
          </Link>
          <Link to="/subscriptions" className="mobile-nav-link" onClick={closeMobileMenu}>
            Subscriptions
          </Link>
          <Link to="/locations" className="mobile-nav-link" onClick={closeMobileMenu}>
            Locations
          </Link>
        </>
      );
    } else if (isCoach(user)) {
      return (
        <>
          <Link to="/dashboard" className="mobile-nav-link" onClick={closeMobileMenu}>
            {t('nav.dashboard')}
          </Link>
          <Link to="/clients" className="mobile-nav-link" onClick={closeMobileMenu}>
            {t('nav.clients')}
          </Link>
          <Link to="/programs" className="mobile-nav-link" onClick={closeMobileMenu}>
            {t('nav.programs')}
          </Link>
          <Link to="/program-builder" className="mobile-nav-link" onClick={closeMobileMenu}>
            {t('nav.programBuilder')}
          </Link>
        </>
      );
    } else if (isClient(user)) {
      return (
        <>
          <Link to="/dashboard" className="mobile-nav-link" onClick={closeMobileMenu}>
            {t('nav.dashboard')}
          </Link>
          <Link to="/my-programs" className="mobile-nav-link" onClick={closeMobileMenu}>
            My Programs
          </Link>
          <Link to="/progress" className="mobile-nav-link" onClick={closeMobileMenu}>
            Progress
          </Link>
        </>
      );
    }
    return null;
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-brand">
          <h1>{t('app.name')}</h1>
          <span className="header-tagline">{t('app.tagline')}</span>
        </div>

        <nav className="header-nav">
          {renderNavLinks()}
        </nav>

        <div className="header-actions">
          <button onClick={toggleLanguage} className="lang-button">
            {i18n.language === 'en' ? 'ES' : 'EN'}
          </button>
          <button onClick={handleLogout} className="logout-button">
            {t('nav.signOut')}
          </button>
        </div>

        <button
          className={`mobile-menu-button ${isMobileMenuOpen ? 'open' : ''}`}
          onClick={toggleMobileMenu}
          aria-label="Toggle menu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>

      {/* Mobile Menu */}
      <div className={`mobile-menu ${isMobileMenuOpen ? 'open' : ''}`}>
        <nav className="mobile-nav">
          {renderMobileNavLinks()}
        </nav>

        <div className="mobile-actions">
          <button onClick={toggleLanguage} className="mobile-lang-button">
            {i18n.language === 'en' ? 'ES' : 'EN'}
          </button>
          <button onClick={handleLogout} className="mobile-logout-button">
            {t('nav.signOut')}
          </button>
        </div>
      </div>
    </header>
  );
}
