import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './Header.css';

export default function Header() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'es' : 'en';
    i18n.changeLanguage(newLang);
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
      </div>
    </header>
  );
}
