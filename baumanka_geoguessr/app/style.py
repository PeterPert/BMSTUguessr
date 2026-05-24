from app.theme import build_stylesheet, default_colors, load_theme

# Сохраняем совместимость: APP_STYLE — дефолтная тема до load_theme().
APP_STYLE = build_stylesheet(default_colors())

__all__ = ["APP_STYLE", "build_stylesheet", "default_colors", "load_theme"]
