class Job {
  final String id;
  final String title;
  final String? company;
  final String? location;
  final String? snippet;
  final double matchScore;
  final String? applyUrl;
  final String? logoUrl;
  final String? salaryRange;
  final String? type;
  final List<String> skills;

  Job({
    required this.id,
    required this.title,
    this.company,
    this.location,
    this.snippet,
    required this.matchScore,
    this.applyUrl,
    this.logoUrl,
    this.salaryRange,
    this.type,
    this.skills = const [],
  });

  factory Job.fromJson(Map<String, dynamic> json) {
    return Job(
      id: json['id'] as String,
      title: json['title'] as String,
      company: json['company'] as String?,
      location: json['location'] as String?,
      snippet: json['snippet'] as String?,
      matchScore: (json['score'] as num).toDouble(),
      applyUrl: json['apply_url'] as String?,
      logoUrl: json['logo_url'] as String?,
      salaryRange: json['salary_range'] as String?,
      type: json['type'] as String?,
      skills: (json['skills'] as List<dynamic>?)?.map((e) => e as String).toList() ?? const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'company': company,
      'location': location,
      'snippet': snippet,
      'score': matchScore,
      'apply_url': applyUrl,
      'logo_url': logoUrl,
      'salary_range': salaryRange,
      'type': type,
      'skills': skills,
    };
  }
}

class JobMatch extends Job {
  final MatchMetadata metadata;

  JobMatch({
    required String id,
    required String title,
    String? company,
    String? location,
    String? snippet,
    required double matchScore,
    String? applyUrl,
    String? logoUrl,
    String? salaryRange,
    String? type,
    List<String> skills = const [],
    required this.metadata,
  }) : super(
          id: id,
          title: title,
          company: company,
          location: location,
          snippet: snippet,
          matchScore: matchScore,
          applyUrl: applyUrl,
          logoUrl: logoUrl,
          salaryRange: salaryRange,
          type: type,
          skills: skills,
        );

  factory JobMatch.fromJson(Map<String, dynamic> json) {
    return JobMatch(
      id: json['id'] as String,
      title: json['title'] as String,
      company: json['company'] as String?,
      location: json['location'] as String?,
      snippet: json['snippet'] as String?,
      matchScore: (json['score'] as num).toDouble(),
      applyUrl: json['apply_url'] as String?,
      logoUrl: json['logo_url'] as String?,
      salaryRange: json['salary_range'] as String?,
      type: json['type'] as String?,
      skills: (json['skills'] as List<dynamic>?)?.map((e) => e as String).toList() ?? const [],
      metadata: MatchMetadata.fromJson(json['metadata'] as Map<String, dynamic>),
    );
  }
}

class MatchMetadata {
  final double bm25Score;
  final bool hasSkillMatch;
  final bool hasLocationMatch;

  MatchMetadata({
    required this.bm25Score,
    required this.hasSkillMatch,
    required this.hasLocationMatch,
  });

  factory MatchMetadata.fromJson(Map<String, dynamic> json) {
    return MatchMetadata(
      bm25Score: (json['bm25_score'] as num).toDouble(),
      hasSkillMatch: json['has_skill_match'] as bool,
      hasLocationMatch: json['has_location_match'] as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'bm25_score': bm25Score,
      'has_skill_match': hasSkillMatch,
      'has_location_match': hasLocationMatch,
    };
  }
}