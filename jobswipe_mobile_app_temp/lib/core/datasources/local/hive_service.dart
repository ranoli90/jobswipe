import 'package:hive_flutter/hive_flutter.dart';

class HiveService {
  static const String _userPreferencesBox = 'user_preferences';
  static const String _cacheBox = 'cache';
  static const String _settingsBox = 'settings';

  static Future<void> init() async {
    await Hive.initFlutter();

    // Open boxes
    await Hive.openBox(_userPreferencesBox);
    await Hive.openBox(_cacheBox);
    await Hive.openBox(_settingsBox);
  }

  // User Preferences
  Box get _userPreferences => Hive.box(_userPreferencesBox);

  Future<void> setUserPreference(String key, dynamic value) async {
    await _userPreferences.put(key, value);
  }

  dynamic getUserPreference(String key, {dynamic defaultValue}) {
    return _userPreferences.get(key, defaultValue: defaultValue);
  }

  Future<void> removeUserPreference(String key) async {
    await _userPreferences.delete(key);
  }

  Future<void> clearUserPreferences() async {
    await _userPreferences.clear();
  }

  // Cache
  Box get _cache => Hive.box(_cacheBox);

  Future<void> setCache(String key, dynamic value, {Duration? expiry}) async {
    final cacheData = {
      'value': value,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
      'expiry': expiry != null
          ? DateTime.now().add(expiry).millisecondsSinceEpoch
          : null,
    };
    await _cache.put(key, cacheData);
  }

  dynamic getCache(String key) {
    final cacheData = _cache.get(key);
    if (cacheData == null) return null;

    final expiry = cacheData['expiry'];
    if (expiry != null && DateTime.now().millisecondsSinceEpoch > expiry) {
      // Cache expired, remove it
      _cache.delete(key);
      return null;
    }

    return cacheData['value'];
  }

  Future<void> removeCache(String key) async {
    await _cache.delete(key);
  }

  Future<void> clearCache() async {
    await _cache.clear();
  }

  // Settings
  Box get _settings => Hive.box(_settingsBox);

  Future<void> setSetting(String key, dynamic value) async {
    await _settings.put(key, value);
  }

  dynamic getSetting(String key, {dynamic defaultValue}) {
    return _settings.get(key, defaultValue: defaultValue);
  }

  Future<void> removeSetting(String key) async {
    await _settings.delete(key);
  }

  Future<void> clearSettings() async {
    await _settings.clear();
  }

  // Utility methods
  Future<void> clearAll() async {
    await clearUserPreferences();
    await clearCache();
    await clearSettings();
  }

  Future<void> close() async {
    await Hive.close();
  }
}