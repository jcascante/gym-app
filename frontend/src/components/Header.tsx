import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './Header.css';

export default function Header() {
  const { logout } = useAuth();
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

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-brand">
          <h1>{t('app.name')}</h1>
          <span className="header-tagline">{t('app.tagline')}</span>
        </div>

        <nav className="header-nav">
          <Link to="/dashboard" className="nav-link">{t('nav.dashboard')}</Link>
          <Link to="/program-builder" className="nav-link">{t('nav.programBuilder')}</Link>
          <Link to="/programs" className="nav-link">{t('nav.programs')}</Link>
          <Link to="/clients" className="nav-link">{t('nav.clients')}</Link>
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
          <Link to="/dashboard" className="mobile-nav-link" onClick={closeMobileMenu}>
            {t('nav.dashboard')}
          </Link>
          <Link to="/program-builder" className="mobile-nav-link" onClick={closeMobileMenu}>
            {t('nav.programBuilder')}
          </Link>
          <Link to="/programs" className="mobile-nav-link" onClick={closeMobileMenu}>
            {t('nav.programs')}
          </Link>
          <Link to="/clients" className="mobile-nav-link" onClick={closeMobileMenu}>
            {t('nav.clients')}
          </Link>
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
