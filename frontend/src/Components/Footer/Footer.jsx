import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faGithub } from '@fortawesome/free-brands-svg-icons';
import './Footer.css';

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-content">
        <p className="footer-text">© 2025 RateMyCareer | Data sourced from Reddit</p>
        <a 
          href="https://github.com/AI-Mentorship/RateMyCareer" 
          target="_blank" 
          rel="noopener noreferrer"
          className="github-link"
        >
            <FontAwesomeIcon icon={faGithub} className="github-icon" />
        </a>
      </div>
    </footer>
  );
}

export default Footer;