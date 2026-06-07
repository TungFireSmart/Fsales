# FsalesIOS

SwiftUI iOS project for the first mobile version of FSales.

Current scope:
- Dashboard with lead and quotation metrics.
- Lead list, search, detail, create, edit, and delete.
- Product catalog list, search, detail, create, edit, and delete.
- Quotation list, detail, status update, share text, and create-from-lead flow.
- Quotation lines can be filled from the product catalog or edited manually.
- Local JSON persistence in Application Support.
- App Intent shortcut to open the quotation workflow.

Open `FsalesIOS.xcodeproj` in Xcode and run the `FsalesIOS` scheme on an iOS 17+ simulator.

The GitHub Actions workflow `.github/workflows/ios-build.yml` builds the app on a macOS runner without code signing.
