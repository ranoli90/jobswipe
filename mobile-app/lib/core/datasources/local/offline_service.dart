import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:rxdart/rxcodemart.dart';

/// Service for handling offline data storage and sync
class OfflineService {
  final SharedPreferences _prefs;
  final Connectivity _connectivity;
  
  // Streams
  final _connectionStatusController = BehaviorSubject<ConnectionStatus>();
  Stream<ConnectionStatus> get connectionStatus => _connectionStatusController.stream;
  
  // Keys for storage
  static const String _keyOfflineQueue = 'offline_queue';
  static const String _keyCachedJobs = 'cached_jobs';
  static const String _keyLastSync = 'last_sync';
  static const String _keyOfflineMode = 'offline_mode';
  
  OfflineService(this._prefs, this._connectivity) {
    _initConnectivity();
  }
  
  void _initConnectivity() {
    _connectivity.checkConnectivity().then((status) {
      _connectionStatusController.add(_mapConnectivityStatus(status));
    });
    
    _connectivity.onConnectivityChanged.listen((status) {
      final connectionStatus = _mapConnectivityStatus(status);
      _connectionStatusController.add(connectionStatus);
      
      // Auto-sync when coming back online
      if (connectionStatus == ConnectionStatus.online) {
        _syncPendingChanges();
      }
    });
  }
  
  ConnectionStatus _mapConnectivityStatus(List<ConnectivityResult> results) {
    if (results.contains(ConnectivityResult.mobile) || 
        results.contains(ConnectivityResult.wifi) ||
        results.contains(ConnectivityResult.ethernet)) {
      return ConnectionStatus.online;
    }
    return ConnectionStatus.offline;
  }
  
  /// Check if device is online
  Future<bool> isOnline() async {
    final results = await _connectivity.checkConnectivity();
    return _mapConnectivityStatus(results) == ConnectionStatus.online;
  }
  
  /// Save data for offline access
  Future<void> cacheData(String key, dynamic data) async {
    final jsonData = json.encode(data);
    await _prefs.setString('${_keyCachedJobs}_$key', jsonData);
  }
  
  /// Get cached data
  T? getCachedData<T>(String key, T Function(dynamic) fromJson) {
    final jsonData = _prefs.getString('${_keyCachedJobs}_$key');
    if (jsonData == null) return null;
    
    try {
      final data = json.decode(jsonData);
      return fromJson(data);
    } catch (e) {
      return null;
    }
  }
  
  /// Queue an action for offline sync
  Future<void> queueAction(OfflineAction action) async {
    final queue = getActionQueue();
    queue.add(action.toJson());
    await _prefs.setStringList(_keyOfflineQueue, queue);
  }
  
  /// Get pending actions
  List<Map<String, dynamic>> getActionQueue() {
    final queue = _prefs.getStringList(_keyOfflineQueue) ?? [];
    return queue.map((e) => json.decode(e) as Map<String, dynamic>).toList();
  }
  
  /// Remove an action from queue
  Future<void> removeAction(String actionId) async {
    final queue = getActionQueue();
    queue.removeWhere((e) => e['id'] == actionId);
    await _prefs.setStringList(_keyOfflineQueue, queue.map((e) => json.encode(e)).toList());
  }
  
  /// Sync pending changes when online
  Future<void> _syncPendingChanges() async {
    final queue = getActionQueue();
    if (queue.isEmpty) return;
    
    // Process queue - in a real app, this would retry failed actions
    // For now, we just clear actions that were added while offline
    // The actual sync logic would be in the repository
    await _prefs.remove(_keyOfflineQueue);
    
    // Update last sync time
    await _prefs.setInt(_keyLastSync, DateTime.now().millisecondsSinceEpoch);
  }
  
  /// Get last sync timestamp
  int? getLastSyncTime() => _prefs.getInt(_keyLastSync);
  
  /// Set offline mode
  Future<void> setOfflineMode(bool enabled) async {
    await _prefs.setBool(_keyOfflineMode, enabled);
  }
  
  /// Check if offline mode is enabled
  bool isOfflineModeEnabled() => _prefs.getBool(_keyOfflineMode) ?? false;
  
  /// Clear all cached data
  Future<void> clearCache() async {
    final keys = _prefs.getKeys().where((k) => k.startsWith(_keyCachedJobs));
    for (final key in keys) {
      await _prefs.remove(key);
    }
    await _prefs.remove(_keyOfflineQueue);
    await _prefs.remove(_keyLastSync);
  }
  
  /// Dispose streams
  void dispose() {
    _connectionStatusController.close();
  }
}

/// Offline action to be synced
class OfflineAction {
  final String id;
  final String type;
  final String endpoint;
  final String method;
  final Map<String, dynamic> data;
  final DateTime createdAt;
  
  OfflineAction({
    required this.id,
    required this.type,
    required this.endpoint,
    required this.method,
    required this.data,
    required this.createdAt,
  });
  
  Map<String, dynamic> toJson() => {
    'id': id,
    'type': type,
    'endpoint': endpoint,
    'method': method,
    'data': data,
    'createdAt': createdAt.toIso8601String(),
  };
  
  factory OfflineAction.fromJson(Map<String, dynamic> json) => OfflineAction(
    id: json['id'],
    type: json['type'],
    endpoint: json['endpoint'],
    method: json['method'],
    data: Map<String, dynamic>.from(json['data']),
    createdAt: DateTime.parse(json['createdAt']),
  );
}

/// Connection status enum
enum ConnectionStatus {
  online,
  offline,
}
