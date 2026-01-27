import 'package:flutter/material.dart';

/// JobSwipe Color Palette - Vibrant, Modern, Unique
class AppColors {
  // Primary - Electric Purple Gradient
  static const Color primary = Color(0xFF6C5CE7);
  static const Color primaryDark = Color(0xFF4834D4);
  static const Color primaryLight = Color(0xFFA29BFE);
  
  // Secondary - Vibrant Coral
  static const Color secondary = Color(0xFFFD79A8);
  static const Color secondaryDark = Color(0xFFE84393);
  
  // Accent - Electric Blue
  static const Color accent = Color(0xFF0984E3);
  
  // Success - Mint Green
  static const Color success = Color(0xFF00B894);
  static const Color successLight = Color(0xFF55EFC4);
  
  // Warning - Sunny Yellow
  static const Color warning = Color(0xFFFDCB6E);
  static const Color warningDark = Color(0xFFE1B12C);
  
  // Error - Coral Red
  static const Color error = Color(0xFFD63031);
  static const Color errorLight = Color(0xFFFF7675);
  
  // Neutral - Modern Grays
  static const Color background = Color(0xFFF8F9FA);
  static const Color backgroundDark = Color(0xFF1A1D23);
  
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceDark = Color(0xFF2D3436);
  
  static const Color textPrimary = Color(0xFF2D3436);
  static const Color textPrimaryDark = Color(0xFFFFFFFF);
  
  static const Color textSecondary = Color(0xFF636E72);
  static const Color textSecondaryDark = Color(0xFFB2BEC3);
  
  static const Color divider = Color(0xFFDFE6E9);
  static const Color dividerDark = Color(0xFF636E72);
  
  // Gradients
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primaryLight, primary],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient secondaryGradient = LinearGradient(
    colors: [secondaryDark, secondary],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient successGradient = LinearGradient(
    colors: [successLight, success],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  // Match Score Colors
  static Color getMatchScoreColor(double score) {
    if (score >= 0.8) return success;
    if (score >= 0.6) return primary;
    if (score >= 0.4) return warning;
    return error;
  }
}
