import { useTranslation } from 'react-i18next';
import './Footer.css';

export default function Footer() {
  const { t } = useTranslation();
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-section">
          <h3>{t('app.name')}</h3>
          <p>{t('footer.tagline')}</p>
        </div>

        <div className="footer-section">
          <h4>{t('footer.quickLinks')}</h4>
          <ul>
            <li><a href="#">{t('nav.dashboard')}</a></li>
            <li><a href="#">{t('nav.programs')}</a></li>
            <li><a href="#">{t('nav.clients')}</a></li>
            <li><a href="#">Analytics</a></li>
          </ul>
        </div>

        <div className="footer-section">
          <h4>{t('footer.support')}</h4>
          <ul>
            <li><a href="#">{t('footer.helpCenter')}</a></li>
            <li><a href="#">{t('footer.contactUs')}</a></li>
            <li><a href="#">{t('footer.privacyPolicy')}</a></li>
            <li><a href="#">{t('footer.termsOfService')}</a></li>
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <p>&copy; {currentYear} {t('app.name')}. {t('footer.allRightsReserved')}</p>
      </div>
    </footer>
  );
}
