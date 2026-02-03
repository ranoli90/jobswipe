import 'package:flutter/material.dart';
import 'app_colors.dart';
import 'app_typography.dart';
import 'app_tokens.dart';

/// JobSwipe App Theme - Modern, Brandable, Unique
class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: _lightColorScheme,
      scaffoldBackgroundColor: AppColors.background,
      cardColor: AppColors.surface,
      dividerColor: AppColors.divider,
      
      // Typography
      textTheme: _textTheme,
      
      // App Bar Theme
      appBarTheme: _appBarTheme,
      
      // Card Theme
      cardTheme: _cardTheme,
      
      // Elevated Button Theme
      elevatedButtonTheme: _elevatedButtonTheme,
      
      // Text Button Theme
      textButtonTheme: _textButtonTheme,
      
      // Input Decoration Theme
      inputDecorationTheme: _inputDecorationTheme,
      
      // Icon Theme
      iconTheme: _iconTheme,
      
      // Bottom Navigation Bar Theme
      navigationBarTheme: _navigationBarTheme,
    );
  }
  
  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: _darkColorScheme,
      scaffoldBackgroundColor: AppColors.backgroundDark,
      cardColor: AppColors.surfaceDark,
      dividerColor: AppColors.dividerDark,
      
      // Typography
      textTheme: _darkTextTheme,
      
      // App Bar Theme
      appBarTheme: _darkAppBarTheme,
      
      // Card Theme
      cardTheme: _darkCardTheme,
      
      // Elevated Button Theme
      elevatedButtonTheme: _darkElevatedButtonTheme,
      
      // Text Button Theme
      textButtonTheme: _darkTextButtonTheme,
      
      // Input Decoration Theme
      inputDecorationTheme: _darkInputDecorationTheme,
      
      // Icon Theme
      iconTheme: _darkIconTheme,
      
      // Bottom Navigation Bar Theme
      navigationBarTheme: _darkNavigationBarTheme,
    );
  }
  
  // Light Color Scheme
  static ColorScheme get _lightColorScheme {
    return ColorScheme.light(
      primary: AppColors.primary,
      onPrimary: Colors.white,
      secondary: AppColors.secondary,
      onSecondary: Colors.white,
      error: AppColors.error,
      onError: Colors.white,
      surface: AppColors.surface,
      onSurface: AppColors.textPrimary,
    );
  }
  
  // Dark Color Scheme
  static ColorScheme get _darkColorScheme {
    return ColorScheme.dark(
      primary: AppColors.primary,
      onPrimary: Colors.white,
      secondary: AppColors.secondary,
      onSecondary: Colors.white,
      error: AppColors.error,
      onError: Colors.white,
      surface: AppColors.surfaceDark,
      onSurface: AppColors.textPrimaryDark,
    );
  }
  
  // Text Theme
  static TextTheme get _textTheme {
    return TextTheme(
      displayLarge: AppTypography.displayLarge.copyWith(
        color: AppColors.textPrimary,
      ),
      displayMedium: AppTypography.displayMedium.copyWith(
        color: AppColors.textPrimary,
      ),
      displaySmall: AppTypography.displaySmall.copyWith(
        color: AppColors.textPrimary,
      ),
      headlineLarge: AppTypography.headlineLarge.copyWith(
        color: AppColors.textPrimary,
      ),
      headlineMedium: AppTypography.headlineMedium.copyWith(
        color: AppColors.textPrimary,
      ),
      headlineSmall: AppTypography.headlineSmall.copyWith(
        color: AppColors.textPrimary,
      ),
      titleLarge: AppTypography.titleLarge.copyWith(
        color: AppColors.textPrimary,
      ),
      titleMedium: AppTypography.titleMedium.copyWith(
        color: AppColors.textPrimary,
      ),
      titleSmall: AppTypography.titleSmall.copyWith(
        color: AppColors.textSecondary,
      ),
      bodyLarge: AppTypography.bodyLarge.copyWith(
        color: AppColors.textPrimary,
      ),
      bodyMedium: AppTypography.bodyMedium.copyWith(
        color: AppColors.textPrimary,
      ),
      bodySmall: AppTypography.bodySmall.copyWith(
        color: AppColors.textSecondary,
      ),
      labelLarge: AppTypography.labelLarge.copyWith(
        color: AppColors.textPrimary,
      ),
      labelMedium: AppTypography.labelMedium.copyWith(
        color: AppColors.textSecondary,
      ),
      labelSmall: AppTypography.labelSmall.copyWith(
        color: AppColors.textSecondary,
      ),
    );
  }
  
  // Dark Text Theme
  static TextTheme get _darkTextTheme {
    return TextTheme(
      displayLarge: AppTypography.displayLarge.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      displayMedium: AppTypography.displayMedium.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      displaySmall: AppTypography.displaySmall.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      headlineLarge: AppTypography.headlineLarge.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      headlineMedium: AppTypography.headlineMedium.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      headlineSmall: AppTypography.headlineSmall.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      titleLarge: AppTypography.titleLarge.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      titleMedium: AppTypography.titleMedium.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      titleSmall: AppTypography.titleSmall.copyWith(
        color: AppColors.textSecondaryDark,
      ),
      bodyLarge: AppTypography.bodyLarge.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      bodyMedium: AppTypography.bodyMedium.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      bodySmall: AppTypography.bodySmall.copyWith(
        color: AppColors.textSecondaryDark,
      ),
      labelLarge: AppTypography.labelLarge.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      labelMedium: AppTypography.labelMedium.copyWith(
        color: AppColors.textSecondaryDark,
      ),
      labelSmall: AppTypography.labelSmall.copyWith(
        color: AppColors.textSecondaryDark,
      ),
    );
  }
  
  // App Bar Theme
  static AppBarTheme get _appBarTheme {
    return AppBarTheme(
      elevation: 0,
      centerTitle: true,
      backgroundColor: Colors.transparent,
      foregroundColor: AppColors.textPrimary,
      titleTextStyle: AppTypography.headlineSmall.copyWith(
        color: AppColors.textPrimary,
      ),
      iconTheme: IconThemeData(
        color: AppColors.textPrimary,
        size: AppTokens.iconMd,
      ),
    );
  }
  
  static AppBarTheme get _darkAppBarTheme {
    return AppBarTheme(
      elevation: 0,
      centerTitle: true,
      backgroundColor: Colors.transparent,
      foregroundColor: AppColors.textPrimaryDark,
      titleTextStyle: AppTypography.headlineSmall.copyWith(
        color: AppColors.textPrimaryDark,
      ),
      iconTheme: IconThemeData(
        color: AppColors.textPrimaryDark,
        size: AppTokens.iconMd,
      ),
    );
  }
  
  // Card Theme
  static CardThemeData get _cardTheme {
    return CardThemeData(
      elevation: AppTokens.elevationSm,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppTokens.radiusLg),
      ),
      color: AppColors.surface,
      shadowColor: Colors.black.withOpacity(0.05),
    );
  }
  
  static CardThemeData get _darkCardTheme {
    return CardThemeData(
      elevation: AppTokens.elevationSm,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppTokens.radiusLg),
      ),
      color: AppColors.surfaceDark,
      shadowColor: Colors.black.withOpacity(0.3),
    );
  }
  
  // Elevated Button Theme
  static ElevatedButtonThemeData get _elevatedButtonTheme {
    return ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        textStyle: AppTypography.labelLarge,
        minimumSize: Size(AppTokens.buttonHeightMd, AppTokens.buttonHeightMd),
        padding: EdgeInsets.symmetric(
          horizontal: AppTokens.spacingLg,
          vertical: AppTokens.spacingMd,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        ),
        elevation: AppTokens.elevationSm,
      ),
    );
  }
  
  static ElevatedButtonThemeData get _darkElevatedButtonTheme {
    return ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        textStyle: AppTypography.labelLarge,
        minimumSize: Size(AppTokens.buttonHeightMd, AppTokens.buttonHeightMd),
        padding: EdgeInsets.symmetric(
          horizontal: AppTokens.spacingLg,
          vertical: AppTokens.spacingMd,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        ),
        elevation: AppTokens.elevationSm,
      ),
    );
  }
  
  // Text Button Theme
  static TextButtonThemeData get _textButtonTheme {
    return TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: AppColors.primary,
        textStyle: AppTypography.labelMedium,
        padding: EdgeInsets.symmetric(
          horizontal: AppTokens.spacingMd,
          vertical: AppTokens.spacingSm,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppTokens.radiusSm),
        ),
      ),
    );
  }
  
  static TextButtonThemeData get _darkTextButtonTheme {
    return TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: AppColors.primary,
        textStyle: AppTypography.labelMedium,
        padding: EdgeInsets.symmetric(
          horizontal: AppTokens.spacingMd,
          vertical: AppTokens.spacingSm,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppTokens.radiusSm),
        ),
      ),
    );
  }
  
  // Input Decoration Theme
  static InputDecorationTheme get _inputDecorationTheme {
    return InputDecorationTheme(
      filled: true,
      fillColor: AppColors.background,
      contentPadding: EdgeInsets.symmetric(
        horizontal: AppTokens.spacingMd,
        vertical: AppTokens.spacingMd,
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        borderSide: BorderSide(color: AppColors.divider),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        borderSide: BorderSide(color: AppColors.primary, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        borderSide: BorderSide(color: AppColors.error),
      ),
      hintStyle: AppTypography.bodyMedium.copyWith(
        color: AppColors.textSecondary,
      ),
      labelStyle: AppTypography.labelMedium.copyWith(
        color: AppColors.textSecondary,
      ),
    );
  }
  
  static InputDecorationTheme get _darkInputDecorationTheme {
    return InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surfaceDark,
      contentPadding: EdgeInsets.symmetric(
        horizontal: AppTokens.spacingMd,
        vertical: AppTokens.spacingMd,
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        borderSide: BorderSide(color: AppColors.dividerDark),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        borderSide: BorderSide(color: AppColors.primary, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.radiusMd),
        borderSide: BorderSide(color: AppColors.error),
      ),
      hintStyle: AppTypography.bodyMedium.copyWith(
        color: AppColors.textSecondaryDark,
      ),
      labelStyle: AppTypography.labelMedium.copyWith(
        color: AppColors.textSecondaryDark,
      ),
    );
  }
  
  // Icon Theme
  static IconThemeData get _iconTheme {
    return IconThemeData(
      color: AppColors.textSecondary,
      size: AppTokens.iconMd,
    );
  }
  
  static IconThemeData get _darkIconTheme {
    return IconThemeData(
      color: AppColors.textSecondaryDark,
      size: AppTokens.iconMd,
    );
  }
  
  // Navigation Bar Theme
  static NavigationBarThemeData get _navigationBarTheme {
    return NavigationBarThemeData(
      elevation: AppTokens.elevationLg,
      backgroundColor: AppColors.surface,
      indicatorColor: AppColors.primary.withOpacity(0.1),
      labelTextStyle: MaterialStatePropertyAll(
        AppTypography.labelSmall.copyWith(
          color: AppColors.textSecondary,
        ),
      ),
      iconTheme: MaterialStatePropertyAll(
        IconThemeData(
          color: AppColors.textSecondary,
          size: AppTokens.iconMd,
        ),
      ),
    );
  }
  
  static NavigationBarThemeData get _darkNavigationBarTheme {
    return NavigationBarThemeData(
      elevation: AppTokens.elevationLg,
      backgroundColor: AppColors.surfaceDark,
      indicatorColor: AppColors.primary.withOpacity(0.1),
      labelTextStyle: MaterialStatePropertyAll(
        AppTypography.labelSmall.copyWith(
          color: AppColors.textSecondaryDark,
        ),
      ),
      iconTheme: MaterialStatePropertyAll(
        IconThemeData(
          color: AppColors.textSecondaryDark,
          size: AppTokens.iconMd,
        ),
      ),
    );
  }
}
