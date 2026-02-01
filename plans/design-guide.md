# JobSwipe Design Guide

## Brand Identity

### Core Values
- **Modern**: Cutting-edge technology meets elegant design
- **Efficient**: Simplify the job application process
- **Bold**: Stand out from traditional job platforms
- **Human**: Approachable and intuitive user experience

### Logo Concept
- Dynamic swipe-inspired logo
- Modern typography with subtle gradient
- Reflects the "swipe to apply" interaction
- Available in light and dark versions

## Color Palette

### Primary Colors
```dart
// Vibrant Coral - Energetic and attention-grabbing
const Color primary = Color(0xFFFF6B6B);
const Color primaryDark = Color(0xFFEE5A6F);
const Color primaryLight = Color(0xFFFF8E8E);

// Teal Blue - Calming and professional
const Color secondary = Color(0xFF4ECDC4);
const Color secondaryDark = Color(0xFF26A69A);
const Color secondaryLight = Color(0xFF67E0D4);

// Sunset Yellow - Optimistic and energetic
const Color accent = Color(0xFFFECA57);
const Color accentDark = Color(0xFFF39C12);
const Color accentLight = Color(0xFFFFE066);
```

### Neutral Colors
```dart
// Background colors
const Color background = Color(0xFFF8F9FA);
const Color backgroundDark = Color(0xFF1A1D23);

// Surface colors
const Color surface = Color(0xFFFFFFFF);
const Color surfaceDark = Color(0xFF2D3436);

// Text colors
const Color textPrimary = Color(0xFF2D3436);
const Color textPrimaryDark = Color(0xFFFFFFFF);
const Color textSecondary = Color(0xFF636E72);
const Color textSecondaryDark = Color(0xFFB2BEC3);

// Divider colors
const Color divider = Color(0xFFDFE6E9);
const Color dividerDark = Color(0xFF636E72);
```

### Gradients
```dart
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

static const LinearGradient accentGradient = LinearGradient(
  colors: [accentLight, accent],
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
);
```

## Typography

### Font Family
- **Primary Font**: Inter (Google Fonts) - Modern, clean, versatile
- **Secondary Font**: Poppins (Google Fonts) - Bold, distinctive for headings

### Typography System
```dart
// Display - Largest text, for hero sections
static const TextStyle displayLarge = TextStyle(
  fontSize: 57,
  fontWeight: FontWeight.w700,
  letterSpacing: -0.25,
  height: 1.12,
  fontFamily: 'Poppins',
);

// Headline - For page titles
static const TextStyle headlineLarge = TextStyle(
  fontSize: 32,
  fontWeight: FontWeight.w600,
  letterSpacing: 0,
  height: 1.25,
  fontFamily: 'Poppins',
);

// Title - For section headers
static const TextStyle titleLarge = TextStyle(
  fontSize: 22,
  fontWeight: FontWeight.w600,
  letterSpacing: 0,
  height: 1.27,
  fontFamily: 'Inter',
);

// Body - For main content
static const TextStyle bodyLarge = TextStyle(
  fontSize: 16,
  fontWeight: FontWeight.w400,
