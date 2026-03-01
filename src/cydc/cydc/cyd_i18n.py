#!/usr/bin/env python3

"""
ChooseYourDestiny Internationalization (i18n) Module
Provides unified language support across all CYD tools.

Supports:
- Language selection via CYD_LANG environment variable
- Fallback to system locale
- Language auto-detection (en, es supported)
- Dynamic language switching at runtime

Usage:
    from cyd_i18n import setup_i18n, set_language, _
    
    # In your tool's main() function:
    setup_i18n("tool_name", locale_dir="locale")
    
    # Now use _("translatable string")
    
    # To switch language at runtime:
    set_language("es")
    print(_("Hola"))  # Now in Spanish
"""

import os
import sys
import gettext
import locale as _locale
from pathlib import Path


# Supported languages
SUPPORTED_LANGUAGES = ['en', 'es']

# Language mappings (system locale -> CYD language)
LOCALE_MAPPINGS = {
    'es': 'es',
    'es_ES': 'es',
    'es_MX': 'es',
    'en': 'en',
    'en_US': 'en',
    'en_GB': 'en',
}

# Global state for runtime language switching
_current_language = None
_current_tool_name = None
_current_locale_dir = None
_current_translation = None


def get_system_language():
    """
    Detect system language from locale settings.
    Returns language code (en, es) or None if unsupported.
    """
    try:
        # Try to get language from LC_ALL first, then LANG
        lang_string = _locale.getlocale()[0] or _locale.getdefaultlocale()[0] or ''
        
        if lang_string:
            # Extract language code (e.g., 'es' from 'es_ES.UTF-8')
            lang_code = lang_string.split('_')[0].split('.')[0].lower()
            
            # Check direct mapping
            if lang_code in LOCALE_MAPPINGS:
                return LOCALE_MAPPINGS[lang_code]
            
            # Check if it's a supported language code
            if lang_code in SUPPORTED_LANGUAGES:
                return lang_code
    except Exception:
        pass
    
    return None


def get_language():
    """
    Get the language to use, in order of priority:
    1. CYD_LANG environment variable
    2. System locale detection
    3. Default to English
    """
    # Check environment variable
    lang = os.environ.get('CYD_LANG', '').lower().strip()
    if lang and lang in SUPPORTED_LANGUAGES:
        return lang
    
    # Try system language
    sys_lang = get_system_language()
    if sys_lang:
        return sys_lang
    
    # Default to English
    return 'en'


def setup_i18n(tool_name, locale_dir=None, language=None):
    """
    Initialize internationalization for a tool.
    
    Args:
        tool_name (str): Name of the tool (e.g., 'make_adventure', 'cydc')
        locale_dir (str): Path to locale directory. If None, uses current script's directory
        language (str): Force specific language (en/es). If None, auto-detect.
    
    Returns:
        callable: Translation function (_)
    
    Example:
        _ = setup_i18n('make_adventure', locale_dir='locale')
        print(_("Hello"))  # "Hola" if Spanish, "Hello" if English
    """
    global _current_language, _current_tool_name, _current_locale_dir, _current_translation
    
    # Determine locale directory
    if locale_dir is None:
        locale_dir = os.path.join(os.path.dirname(__file__), 'locale')
    else:
        # Make relative paths absolute from the script's directory
        if not os.path.isabs(locale_dir):
            locale_dir = os.path.join(os.path.dirname(__file__), locale_dir)
    
    # Ensure locale directory exists
    if not os.path.isdir(locale_dir):
        # Fallback to current working directory + locale
        alt_locale_dir = os.path.join(os.getcwd(), 'locale')
        if os.path.isdir(alt_locale_dir):
            locale_dir = alt_locale_dir
        # If still doesn't exist, it will fail gracefully below
    
    # Determine language
    if language is None:
        language = get_language()
    
    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        language = 'en'
    
    # Store configuration for runtime switching
    _current_language = language
    _current_tool_name = tool_name
    _current_locale_dir = locale_dir
    
    # Set up gettext
    try:
        gettext.bindtextdomain(tool_name, locale_dir)
        
        # For language-specific translation
        if language != 'en':
            _current_translation = gettext.translation(
                tool_name,
                localedir=locale_dir,
                languages=[language],
                fallback=True
            )
            _current_translation.install()
            _ = _current_translation.gettext
        else:
            # English: use dummy translation (returns input string)
            gettext.install(tool_name)
            _ = gettext.gettext
    
    except Exception as e:
        # Fallback: return identity function (no translation)
        _ = lambda x: x
    
    return _


def set_language(language):
    """
    Switch to a different language at runtime.
    
    Args:
        language (str): Language code (en/es)
    
    Returns:
        callable: Updated translation function (_)
    
    Example:
        set_language('es')
        print(_("Hello"))  # Now prints "Hola"
    """
    global _current_language, _current_translation
    
    if language not in SUPPORTED_LANGUAGES:
        return lambda x: x
    
    if language == _current_language:
        # Already in this language
        if language != 'en':
            return _current_translation.gettext if _current_translation else gettext.gettext
        else:
            return gettext.gettext
    
    _current_language = language
    
    try:
        if language != 'en' and _current_locale_dir and _current_tool_name:
            _current_translation = gettext.translation(
                _current_tool_name,
                localedir=_current_locale_dir,
                languages=[language],
                fallback=True
            )
            _current_translation.install()
            return _current_translation.gettext
        else:
            # English: return identity function
            _current_translation = None
            return gettext.gettext
    except Exception:
        return lambda x: x


def _(text):
    """
    Dynamic translation function that always uses the current language.
    This allows language switching at runtime without needing to update
    references to the translation function.
    
    Args:
        text (str): Text to translate
    
    Returns:
        str: Translated text in current language
    """
    global _current_translation, _current_language
    
    if _current_translation and _current_language != 'en':
        return _current_translation.gettext(text)
    else:
        return text


def get_available_languages(locale_dir=None):
    """
    Get list of available languages in the locale directory.
    
    Args:
        locale_dir (str): Path to locale directory
    
    Returns:
        list: List of available language codes (e.g., ['en', 'es'])
    """
    if locale_dir is None:
        locale_dir = os.path.join(os.path.dirname(__file__), 'locale')
    
    if not os.path.isdir(locale_dir):
        return ['en']  # Default
    
    languages = ['en']  # English always available (no translation)
    
    try:
        for item in os.listdir(locale_dir):
            item_path = os.path.join(locale_dir, item)
            if os.path.isdir(item_path) and item in SUPPORTED_LANGUAGES:
                if os.path.isdir(os.path.join(item_path, 'LC_MESSAGES')):
                    languages.append(item)
    except Exception:
        pass
    
    return list(set(languages))  # Remove duplicates
