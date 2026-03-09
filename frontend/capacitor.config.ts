import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.swiftreply.app',
  appName: 'SwiftReply',
  webDir: 'dist',
  bundledWebRuntime: false,
  plugins: {
    PushNotifications: { presentationOptions: ['badge', 'sound', 'alert'] },
    SplashScreen: {
      launchShowDuration: 2000,
      launchAutoHide: true,
      backgroundColor: '#0d1117',
      androidSplashResourceName: 'splash',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
    },
    StatusBar: { style: 'dark', backgroundColor: '#0d1117' },
  },
  android: {
    allowMixedContent: false,
    captureInput: true,
    webContentsDebuggingEnabled: false,
    buildOptions: { releaseType: 'APK' },
  },
  ios: {
    contentInset: 'automatic',
    allowsLinkPreview: false,
    limitsNavigationsToAppBoundDomains: true,
  },
};

export default config;
