import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../../../models/job.dart';
import '../../../models/application.dart';

class DatabaseService {
  static final DatabaseService _instance = DatabaseService._internal();
  static Database? _database;

  factory DatabaseService() => _instance;

  DatabaseService._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'jobswipe.db');

    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    // Jobs table
    await db.execute('''
      CREATE TABLE jobs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        company TEXT,
        location TEXT,
        snippet TEXT,
        score REAL NOT NULL,
        apply_url TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
      )
    ''');

    // Applications table
    await db.execute('''
      CREATE TABLE applications (
        id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        status TEXT NOT NULL,
        attempt_count INTEGER DEFAULT 0,
        last_error TEXT,
        assigned_worker TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');

    // Job matches table
    await db.execute('''
      CREATE TABLE job_matches (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        company TEXT,
        location TEXT,
        snippet TEXT,
        score REAL NOT NULL,
        apply_url TEXT,
        bm25_score REAL,
        has_skill_match INTEGER,
        has_location_match INTEGER,
        matched_date TEXT,
        is_viewed INTEGER DEFAULT 0,
        created_at TEXT
      )
    ''');
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    // Handle database upgrades here
  }

  // Job operations
  Future<void> insertJob(Job job) async {
    final db = await database;
    await db.insert(
      'jobs',
      job.toJson(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> insertJobs(List<Job> jobs) async {
    final db = await database;
    final batch = db.batch();

    for (final job in jobs) {
      batch.insert(
        'jobs',
        job.toJson(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);
  }

  Future<List<Job>> getJobs({int? limit, int? offset}) async {
    final db = await database;
    final maps = await db.query(
      'jobs',
      where: 'is_active = ?',
      whereArgs: [1],
      limit: limit,
      offset: offset,
      orderBy: 'created_at DESC',
    );

    return maps.map((map) => Job.fromJson(map)).toList();
  }

  Future<Job?> getJobById(String id) async {
    final db = await database;
    final maps = await db.query(
      'jobs',
      where: 'id = ?',
      whereArgs: [id],
    );

    if (maps.isEmpty) return null;
    return Job.fromJson(maps.first);
  }

  Future<void> updateJob(Job job) async {
    final db = await database;
    await db.update(
      'jobs',
      job.toJson(),
      where: 'id = ?',
      whereArgs: [job.id],
    );
  }

  Future<void> deleteJob(String id) async {
    final db = await database;
    await db.update(
      'jobs',
      {'is_active': 0, 'updated_at': DateTime.now().toIso8601String()},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // Application operations
  Future<void> insertApplication(Application application) async {
    final db = await database;
    await db.insert(
      'applications',
      application.toJson(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Application>> getApplications({String? userId}) async {
    final db = await database;
    final maps = await db.query(
      'applications',
      where: userId != null ? 'user_id = ?' : null,
      whereArgs: userId != null ? [userId] : null,
      orderBy: 'applied_date DESC',
    );

    return maps.map((map) => Application.fromJson(map)).toList();
  }

  Future<Application?> getApplicationById(String id) async {
    final db = await database;
    final maps = await db.query(
      'applications',
      where: 'id = ?',
      whereArgs: [id],
    );

    if (maps.isEmpty) return null;
    return Application.fromJson(maps.first);
  }

  Future<void> updateApplicationStatus(String id, String status) async {
    final db = await database;
    await db.update(
      'applications',
      {'status': status, 'updated_at': DateTime.now().toIso8601String()},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // Job matches operations
  Future<void> insertJobMatch(JobMatch match) async {
    final db = await database;
    final data = {
      'id': match.id,
      'title': match.title,
      'company': match.company,
      'location': match.location,
      'snippet': match.snippet,
      'score': match.score,
      'apply_url': match.applyUrl,
      'bm25_score': match.metadata.bm25Score,
      'has_skill_match': match.metadata.hasSkillMatch ? 1 : 0,
      'has_location_match': match.metadata.hasLocationMatch ? 1 : 0,
      'matched_date': DateTime.now().toIso8601String(),
      'is_viewed': 0,
      'created_at': DateTime.now().toIso8601String(),
    };
    await db.insert(
      'job_matches',
      data,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<JobMatch>> getJobMatches({bool? isViewed}) async {
    final db = await database;
    final whereClauses = <String>[];
    final whereArgs = <dynamic>[];

    if (isViewed != null) {
      whereClauses.add('is_viewed = ?');
      whereArgs.add(isViewed ? 1 : 0);
    }

    final maps = await db.query(
      'job_matches',
      where: whereClauses.isNotEmpty ? whereClauses.join(' AND ') : null,
      whereArgs: whereArgs.isNotEmpty ? whereArgs : null,
      orderBy: 'matched_date DESC',
    );

    return maps.map((map) {
      final metadata = MatchMetadata(
        bm25Score: map['bm25_score'] as double,
        hasSkillMatch: (map['has_skill_match'] as int) == 1,
        hasLocationMatch: (map['has_location_match'] as int) == 1,
      );
      return JobMatch(
        id: map['id'] as String,
        title: map['title'] as String,
        company: map['company'] as String?,
        location: map['location'] as String?,
        snippet: map['snippet'] as String?,
        score: map['score'] as double,
        applyUrl: map['apply_url'] as String?,
        metadata: metadata,
      );
    }).toList();
  }

  Future<void> markMatchAsViewed(String id) async {
    final db = await database;
    await db.update(
      'job_matches',
      {'is_viewed': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // Utility methods
  Future<void> clearAllData() async {
    final db = await database;
    await db.delete('job_matches');
    await db.delete('applications');
    await db.delete('jobs');
  }

  Future<void> close() async {
    final db = await database;
    await db.close();
    _database = null;
  }
}