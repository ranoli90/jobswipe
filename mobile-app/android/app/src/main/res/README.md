# Android App Assets

## App Icons

Replace the default Flutter icons in the `mipmap-*` directories with your custom JobSwipe app icons.

Required icon sizes:
- mipmap-mdpi/ic_launcher.png (48x48)
- mipmap-hdpi/ic_launcher.png (72x72)
- mipmap-xhdpi/ic_launcher.png (96x96)
- mipmap-xxhdpi/ic_launcher.png (144x144)
- mipmap-xxxhdpi/ic_launcher.png (192x192)

## Splash Screen

The splash screen is configured in `drawable/launch_background.xml` with a red background (#FF6B6B).

To add a logo, create a `launch_image.png` file and place it in the appropriate mipmap directories, then update the XML to reference it.

Current configuration shows a red background with space for a centered logo.