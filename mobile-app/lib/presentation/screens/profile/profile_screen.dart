import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:file_picker/file_picker.dart';
import '../../../core/di/service_locator.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../core/theme/app_typography.dart';
import '../../bloc/auth/auth_bloc.dart';
import '../../bloc/profile/profile_bloc.dart';
import '../../models/user.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  final _fullNameController = TextEditingController();
  final _headlineController = TextEditingController();
  final _locationController = TextEditingController();
  final _phoneController = TextEditingController();
  final _skillsController = TextEditingController();

  @override
  void initState() {
    super.initState();
    context.read<ProfileBloc>().add(ProfileLoadRequested());
  }

  @override
  void dispose() {
    _fullNameController.dispose();
    _headlineController.dispose();
    _locationController.dispose();
    _phoneController.dispose();
    _skillsController.dispose();
    super.dispose();
  }

  void _toggleEdit() {
    context.read<ProfileBloc>().add(ProfileEditModeToggled());
  }

  void _handleSave() {
    if (_formKey.currentState!.validate()) {
      context.read<ProfileBloc>().add(
        ProfileUpdateRequested(
          data: {
            'full_name': _fullNameController.text.trim(),
            'headline': _headlineController.text.trim(),
            'location': _locationController.text.trim(),
            'phone': _phoneController.text.trim(),
          },
        ),
      );
    }
  }

  void _addSkill(String skill) {
    final currentState = context.read<ProfileBloc>().state;
    if (currentState is ProfileLoaded) {
      final updatedSkills = List<String>.from(currentState.user.skills)..add(skill);
      context.read<ProfileBloc>().add(ProfileSkillsUpdateRequested(updatedSkills));
      _skillsController.clear();
    } else if (currentState is ProfileUpdated) {
      final updatedSkills = List<String>.from(currentState.user.skills)..add(skill);
      context.read<ProfileBloc>().add(ProfileSkillsUpdateRequested(updatedSkills));
      _skillsController.clear();
    }
  }

  void _removeSkill(String skill) {
    final currentState = context.read<ProfileBloc>().state;
    if (currentState is ProfileLoaded) {
      final updatedSkills = List<String>.from(currentState.user.skills)..remove(skill);
      context.read<ProfileBloc>().add(ProfileSkillsUpdateRequested(updatedSkills));
    } else if (currentState is ProfileUpdated) {
      final updatedSkills = List<String>.from(currentState.user.skills)..remove(skill);
      context.read<ProfileBloc>().add(ProfileSkillsUpdateRequested(updatedSkills));
    }
  }

  Future<void> _handleUploadResume() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'doc', 'docx'],
      allowMultiple: false,
    );

    if (result != null && result.files.isNotEmpty && mounted) {
      final file = result.files.first;
      if (file.path != null) {
        context.read<ProfileBloc>().add(
          ProfileResumeUploadRequested(file.path!),
        );
      }
    }
  }

  void _handleLogout() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Logout'),
        content: const Text('Are you sure you want to logout?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              context.read<AuthBloc>().add(AuthLogoutRequested());
            },
            child: const Text('Logout'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: BlocBuilder<ProfileBloc, ProfileState>(
        builder: (context, state) => AppBar(
          title: Text(
            'Profile',
            style: AppTypography.titleLarge.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w700,
            ),
          ),
          centerTitle: true,
          elevation: 0,
          backgroundColor: AppColors.surface,
          actions: [
            if (state is ProfileLoaded && !state.isEditing)
              IconButton(
                icon: const Icon(Icons.edit_outlined),
                onPressed: _toggleEdit,
              )
            else if (state is ProfileLoaded && state.isEditing)
              IconButton(
                icon: const Icon(Icons.close_outlined),
                onPressed: _toggleEdit,
              )
            else if (state is ProfileUpdated && !state.isEditing)
              IconButton(
                icon: const Icon(Icons.edit_outlined),
                onPressed: _toggleEdit,
              )
            else if (state is ProfileUpdated && state.isEditing)
              IconButton(
                icon: const Icon(Icons.close_outlined),
                onPressed: _toggleEdit,
              ),
          ],
        ),
      ),
      body: BlocListener<ProfileBloc, ProfileState>(
        listener: (context, state) {
          if (state is ProfileUpdated) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: AppColors.success,
              ),
            );
          }

          if (state is ProfileError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: AppColors.error,
              ),
            );
          }
        },
        child: BlocBuilder<ProfileBloc, ProfileState>(
          builder: (context, state) {
            if (state is ProfileLoading) {
              return const Center(
                child: CircularProgressIndicator(),
              );
            }

            if (state is ProfileLoaded || state is ProfileUpdated) {
              final user = state is ProfileLoaded ? state.user : (state as ProfileUpdated).user;
              final isEditing = state is ProfileLoaded ? state.isEditing : (state as ProfileUpdated).isEditing;

              if (!isEditing) {
                _fullNameController.text = user.fullName ?? '';
                _headlineController.text = user.headline ?? '';
                _locationController.text = user.location ?? '';
                _phoneController.text = user.phone ?? '';
              }

              return SingleChildScrollView(
                padding: const EdgeInsets.all(AppTokens.spacingLg),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Avatar
                      Center(
                        child: Stack(
                          children: [
                            CircleAvatar(
                              radius: 50,
                              backgroundColor: AppColors.primary.withOpacity(0.1),
                              child: Text(
                                (user.fullName ?? user.email)
                                    .split(' ')
                                    .map((name) => name[0].toUpperCase())
                                    .take(2)
                                    .join(),
                                style: AppTypography.headlineLarge.copyWith(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            if (isEditing)
                              Positioned(
                                right: 0,
                                bottom: 0,
                                child: Container(
                                  decoration: BoxDecoration(
                                    color: AppColors.primary,
                                    shape: BoxShape.circle,
                                  ),
                                  child: IconButton(
                                    icon: const Icon(
                                      Icons.camera_alt_outlined,
                                      color: Colors.white,
                                    ),
                                    onPressed: _handleUploadResume,
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                      const SizedBox(height: AppTokens.spacingXl),

                      // Email (read-only)
                      _buildReadOnlyField(
                        label: 'Email',
                        value: user.email,
                        icon: Icons.email_outlined,
                      ),
                      const SizedBox(height: AppTokens.spacingMd),

                      // Full name
                      _buildEditableField(
                        label: 'Full Name',
                        controller: _fullNameController,
                        icon: Icons.person_outlined,
                        enabled: isEditing,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter your full name';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: AppTokens.spacingMd),

                      // Headline
                      _buildEditableField(
                        label: 'Headline',
                        controller: _headlineController,
                        icon: Icons.work_outline,
                        enabled: isEditing,
                        maxLines: 2,
                      ),
                      const SizedBox(height: AppTokens.spacingMd),

                      // Location
                      _buildEditableField(
                        label: 'Location',
                        controller: _locationController,
                        icon: Icons.location_on_outlined,
                        enabled: isEditing,
                      ),
                      const SizedBox(height: AppTokens.spacingMd),

                      // Phone
                      _buildEditableField(
                        label: 'Phone',
                        controller: _phoneController,
                        icon: Icons.phone_outlined,
                        enabled: isEditing,
                        keyboardType: TextInputType.phone,
                      ),
                      const SizedBox(height: AppTokens.spacingMd),

                      // Skills
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Skills',
                            style: AppTypography.labelMedium.copyWith(
                              color: AppColors.textSecondary,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: AppTokens.spacingSm),
                          if (isEditing) ...[
                            Row(
                              children: [
                                Expanded(
                                  child: TextField(
                                    controller: _skillsController,
                                    decoration: InputDecoration(
                                      hintText: 'Add a skill',
                                      border: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
                                      ),
                                      contentPadding: const EdgeInsets.symmetric(
                                        horizontal: AppTokens.spacingMd,
                                        vertical: AppTokens.spacingSm,
                                      ),
                                    ),
                                    onSubmitted: (value) {
                                      if (value.trim().isNotEmpty) {
                                        _addSkill(value.trim());
                                      }
                                    },
                                  ),
                                ),
                                const SizedBox(width: AppTokens.spacingSm),
                                IconButton(
                                  onPressed: () {
                                    final skill = _skillsController.text.trim();
                                    if (skill.isNotEmpty) {
                                      _addSkill(skill);
                                    }
                                  },
                                  icon: const Icon(Icons.add),
                                  color: AppColors.primary,
                                ),
                              ],
                            ),
                            const SizedBox(height: AppTokens.spacingSm),
                          ],
                          Wrap(
                            spacing: AppTokens.spacingXs,
                            runSpacing: AppTokens.spacingXs,
                            children: user.skills.map(
                              (skill) => Chip(
                                label: Text(skill),
                                backgroundColor: AppColors.primary.withOpacity(0.1),
                                labelStyle: AppTypography.labelSmall.copyWith(
                                  color: AppColors.primary,
                                ),
                                deleteIcon: isEditing ? const Icon(Icons.close, size: 16) : null,
                                onDeleted: isEditing ? () => _removeSkill(skill) : null,
                              ),
                            ).toList(),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppTokens.spacingLg),

                      // Work experience
                      if (user.workExperience.isNotEmpty)
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Work Experience',
                              style: AppTypography.labelMedium.copyWith(
                                color: AppColors.textSecondary,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: AppTokens.spacingSm),
                            ...user.workExperience.take(3).map((exp) => _buildExperienceCard(exp)),
                          ],
                        ),
                      const SizedBox(height: AppTokens.spacingLg),

                      // Save button
                      if (isEditing)
                        SizedBox(
                          height: 56,
                          child: ElevatedButton(
                            onPressed: _handleSave,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(AppTokens.radiusLg),
                              ),
                              elevation: 0,
                            ),
                            child: Text(
                              'Save Changes',
                              style: AppTypography.titleMedium.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),

                      const SizedBox(height: AppTokens.spacingXl),

                      // Logout button
                      OutlinedButton.icon(
                        onPressed: _handleLogout,
                        icon: const Icon(Icons.logout_outlined),
                        label: 'Logout',
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.error,
                          side: BorderSide(color: AppColors.error),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(AppTokens.radiusMd),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }

            return const SizedBox.shrink();
          },
        ),
      ),
      bottomNavigationBar: _buildBottomNavigationBar(),
    );
  }

  Widget _buildReadOnlyField({
    required String label,
    required String value,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.all(AppTokens.spacingMd),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.textSecondary, size: 20),
          const SizedBox(width: AppTokens.spacingMd),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: AppTypography.labelSmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: AppTypography.bodyLarge.copyWith(
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEditableField({
    required String label,
    required TextEditingController controller,
    required IconData icon,
    required bool enabled,
    int maxLines = 1,
    TextInputType? keyboardType,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      enabled: enabled,
      maxLines: maxLines,
      keyboardType: keyboardType,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        ),
        filled: !enabled,
        fillColor: !enabled ? AppColors.background : null,
      ),
      validator: validator,
    );
  }

  Widget _buildExperienceCard(dynamic exp) {
    return Container(
      margin: const EdgeInsets.only(bottom: AppTokens.spacingMd),
      padding: const EdgeInsets.all(AppTokens.spacingMd),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            exp['title'] ?? 'Position',
            style: AppTypography.titleMedium.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            exp['company'] ?? 'Company',
            style: AppTypography.bodyMedium.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          if (exp['start_date'] != null)
            Padding(
              padding: const EdgeInsets.only(top: AppTokens.spacingSm),
              child: Text(
                '${exp['start_date']} - ${exp['end_date'] ?? 'Present'}',
                style: AppTypography.bodySmall.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildBottomNavigationBar() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: AppTokens.shadowLg,
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: AppTokens.spacingLg,
            vertical: AppTokens.spacingMd,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem(
                icon: Icons.home_outlined,
                label: 'Feed',
                isSelected: false,
                onTap: () {
                  Navigator.of(context).pushNamed('/feed');
                },
              ),
              _buildNavItem(
                icon: Icons.work_outline,
                label: 'Applications',
                isSelected: false,
                onTap: () {
                  Navigator.of(context).pushNamed('/applications');
                },
              ),
              _buildNavItem(
                icon: Icons.person_outline,
                label: 'Profile',
                isSelected: true,
                onTap: () {
                  // Already on profile
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem({
    required IconData icon,
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppTokens.radiusMd),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: AppTokens.spacingMd,
          vertical: AppTokens.spacingSm,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? AppColors.primary : AppColors.textSecondary,
              size: 24,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: AppTypography.labelSmall.copyWith(
                color: isSelected ? AppColors.primary : AppColors.textSecondary,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
