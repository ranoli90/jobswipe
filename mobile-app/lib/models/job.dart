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
  
  // Extended fields for detail view
  final String? description;
  final String? employmentType;
  final String? experienceLevel;
  final String? industry;
  final String? postedDate;
  final String? salary;

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
    this.description,
    this.employmentType,
    this.experienceLevel,
    this.industry,
    this.postedDate,
    this.salary,
  });

  factory Job.fromJson(Map<String, dynamic> json) {
    return Job(
      id: json['id'] as String,
      title: json['title'] as String,
      company: json['company'] as String?,
      location: json['location'] as String?,
      snippet: json['snippet'] as String? ?? json['description'] as String?,
      matchScore: (json['score'] as num?)?.toDouble() ?? 0.0,
      applyUrl: json['apply_url'] as String?,
      logoUrl: json['logo_url'] as String?,
      salaryRange: json['salary_range'] as String? ?? json['salary'] as String?,
      type: json['type'] as String? ?? json['job_type'] as String?,
      skills: (json['skills'] as List<dynamic>?)?.map((e) => e as String).toList() ?? const [],
      description: json['description'] as String?,
      employmentType: json['employment_type'] as String?,
      experienceLevel: json['experience_level'] as String?,
      industry: json['industry'] as String?,
      postedDate: json['posted_date'] as String? ?? json['created_at'] as String?,
      salary: json['salary'] as String? ?? json['salary_range'] as String?,
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
      'description': description,
      'employment_type': employmentType,
      'experience_level': experienceLevel,
      'industry': industry,
      'posted_date': postedDate,
      'salary': salary,
    };
  }

  Job copyWith({
    String? id,
    String? title,
    String? company,
    String? location,
    String? snippet,
    double? matchScore,
    String? applyUrl,
    String? logoUrl,
    String? salaryRange,
    String? type,
    List<String>? skills,
    String? description,
    String? employmentType,
    String? experienceLevel,
    String? industry,
    String? postedDate,
    String? salary,
  }) {
    return Job(
      id: id ?? this.id,
      title: title ?? this.title,
      company: company ?? this.company,
      location: location ?? this.location,
      snippet: snippet ?? this.snippet,
      matchScore: matchScore ?? this.matchScore,
      applyUrl: applyUrl ?? this.applyUrl,
      logoUrl: logoUrl ?? this.logoUrl,
      salaryRange: salaryRange ?? this.salaryRange,
      type: type ?? this.type,
      skills: skills ?? this.skills,
      description: description ?? this.description,
      employmentType: employmentType ?? this.employmentType,
      experienceLevel: experienceLevel ?? this.experienceLevel,
      industry: industry ?? this.industry,
      postedDate: postedDate ?? this.postedDate,
      salary: salary ?? this.salary,
    );
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