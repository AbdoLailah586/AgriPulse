import React, { useEffect, useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, ChevronUp } from 'lucide-react';

const languages = [
    { code: 'en', name: 'English', dir: 'ltr' },
    { code: 'ar', name: 'العربية', dir: 'rtl' },
    { code: 'fr', name: 'Français', dir: 'ltr' },
    { code: 'de', name: 'Deutsch', dir: 'ltr' },
    { code: 'sw', name: 'Kiswahili', dir: 'ltr' },
];

export default function LanguageSwitcher() {
    const { i18n } = useTranslation();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    const currentLang = languages.find((l) => l.code === i18n.language) || languages[0];

    useEffect(() => {
        // Update HTML direction and language
        document.documentElement.dir = currentLang.dir || 'ltr';
        document.documentElement.lang = i18n.language;

        if (currentLang.dir === 'rtl') {
            document.body.classList.add('rtl');
            document.body.classList.remove('ltr');
        } else {
            document.body.classList.add('ltr');
            document.body.classList.remove('rtl');
        }
    }, [i18n.language, currentLang]);

    // Close when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const changeLanguage = (langCode) => {
        i18n.changeLanguage(langCode);
        setIsOpen(false);
    };

    return (
        <div className="language-switcher-container" ref={dropdownRef} style={{ position: 'relative', width: '100%' }}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg border transition-all text-xs font-semibold"
                style={{
                    backgroundColor: isOpen ? 'rgba(23, 63, 53, 0.08)' : 'transparent',
                    borderColor: isOpen ? '#173F35' : 'var(--border-subtle, #E6E5DC)',
                    color: isOpen ? '#173F35' : 'var(--text-secondary, #858A80)'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Globe size={15} style={{ color: isOpen ? '#173F35' : 'var(--text-muted, #9EABA5)' }} />
                    <span style={{ fontSize: '12px', fontWeight: '600' }}>{currentLang.name}</span>
                </div>
                <ChevronUp
                    size={14}
                    style={{
                        transition: 'transform 0.2s ease',
                        transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                        opacity: 0.7
                    }}
                />
            </button>

            {isOpen && (
                <div className="language-dropdown-menu" style={{
                    position: 'absolute',
                    bottom: 'calc(100% + 6px)',
                    left: 0,
                    right: 0,
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #D8D7CD',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px rgba(23, 63, 53, 0.12)',
                    zIndex: 2000,
                    overflow: 'hidden',
                    animation: 'dropdownFadeIn 200ms cubic-bezier(0, 0, 0.2, 1)'
                }}>
                    <div style={{ padding: '4px' }}>
                        {languages.map((lang) => (
                            <button
                                key={lang.code}
                                onClick={() => changeLanguage(lang.code)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    width: '100%',
                                    padding: '8px 10px',
                                    background: lang.code === i18n.language ? 'rgba(23, 63, 53, 0.08)' : 'transparent',
                                    border: 'none',
                                    borderRadius: '8px',
                                    color: lang.code === i18n.language ? '#173F35' : '#252B28',
                                    fontSize: '12px',
                                    fontWeight: lang.code === i18n.language ? '700' : '500',
                                    cursor: 'pointer',
                                    textAlign: 'left',
                                    transition: 'all 0.15s ease'
                                }}
                                onMouseEnter={(e) => {
                                    if (lang.code !== i18n.language) {
                                        e.currentTarget.style.backgroundColor = 'rgba(23, 63, 53, 0.04)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (lang.code !== i18n.language) {
                                        e.currentTarget.style.backgroundColor = 'transparent';
                                    }
                                }}
                            >
                                <span>{lang.name}</span>
                                {lang.code === i18n.language && (
                                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#173F35' }} />
                                )}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            <style>{`
                @keyframes dropdownFadeIn {
                    from { opacity: 0; transform: translateY(10px) scale(0.95); }
                    to { opacity: 1; transform: translateY(0) scale(1); }
                }
            `}</style>
        </div>
    );
}
