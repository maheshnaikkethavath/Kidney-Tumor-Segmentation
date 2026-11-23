# Frontend - React/Vite Medical Dashboard

Premium dark-mode React dashboard for kidney and tumor segmentation analysis.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Development server will be available at: `http://localhost:5173`

## Build & Deployment

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── App.jsx                 # Main application component
├── main.jsx               # React entry point
├── index.css              # Tailwind CSS styles
├── components/
│   ├── Header.jsx         # App header with branding
│   ├── ImageUpload.jsx    # File upload component
│   ├── ImageDisplay.jsx   # Image comparison view
│   ├── AnalysisResults.jsx # Segmentation metrics
│   └── ReportGenerator.jsx # Report controls
└── utils/
    └── api.js             # API client functions
```

## Components

### Header
- Application branding
- Medical aesthetic (teal/dark-blue)
- Sticky header for navigation

### ImageUpload
- Drag-and-drop file upload
- File validation (PNG/JPG, <10MB)
- Loading indicator
- Input requirements display

### ImageDisplay
- Side-by-side comparison view
- Original vs. Segmentation (with configurable opacity)
- Attention heatmap display
- Color legend (Black=Background, Cyan=Kidney, Red=Tumor)

### AnalysisResults
- Tumor detection status with warning/success icons
- Quantitative metrics (area in pixels and cm²)
- Tumor coverage percentage
- Class distribution progress bars
- Clinical notes and disclaimers

### ReportGenerator
- Report format selection (HTML/Markdown)
- Download functionality
- Integration with backend API

## Styling

### Tailwind Configuration
- Custom color scheme: Medical navy, dark blue, teal, cyan
- Extended with medical-specific colors
- System font stack for accessibility

### Color Palette
- **Background**: `#0f172a` (Medical Navy)
- **Dark**: `#1e293b` (Darker Navy)
- **Teal**: `#06b6d4` (Cyan)
- **Accent**: `#0ea5e9` (Light Blue)

### Component Styles
- `.btn-primary`: Teal buttons (primary actions)
- `.btn-secondary`: Dark buttons with teal border
- `.card`: Dark card background with teal border
- `.input-field`: Styled input fields
- `.label`: Form labels

## API Integration

### API Client (utils/api.js)

#### Functions
- `healthCheck()`: Verify backend is running
- `predictSegmentation(file)`: Get segmentation prediction
- `generateGradCAM(file, targetClass)`: Generate attention heatmap
- `generateReport(file, patientId, patientName, format)`: Create medical report

#### Configuration
```javascript
API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

Environment variable in `.env.local`:
```
VITE_API_URL=http://localhost:8000
```

## State Management

### App.jsx State
- `uploadedImage`: Base64 data URL of uploaded image
- `predictions`: Segmentation results and metrics
- `heatmap`: GradCAM attention visualization
- `loading`: API request status
- `error`: Error messages
- `maskOpacity`: Segmentation mask transparency (0-100%)
- `activeTab`: Current view (segmentation/heatmap)

### Data Flow
1. User uploads image → ImageUpload component → App state
2. API call to /predict endpoint
3. Results stored in predictions state
4. ImageDisplay renders with mask overlay
5. AnalysisResults shows metrics

## Features

### Image Upload
- Drag and drop support
- File type validation (PNG, JPG)
- File size limit (10MB)
- Loading indicator during processing
- Error handling with user messages

### Segmentation Analysis
- Original CT slice display
- Color-coded segmentation mask
- Adjustable mask opacity slider
- Class distribution visualization
- Tumor detection indication

### Attention Heatmap
- GradCAM visualization for Tumor class
- Overlay on original image
- Helps understand model decisions
- Color-mapped intensity display

### Report Generation
- HTML format (printable, styled)
- Markdown format (text-based)
- Embedded images
- Patient information fields
- Clinical recommendations

## Responsive Design

Breakpoints:
- Mobile: Full-width single column
- Tablet: 2-column layout
- Desktop: 3-column layout (upload controls, image, analysis)

## Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- Color contrast ratio > 4.5:1
- Keyboard navigation support
- Alt text for all images

## Performance

- Lazy loading of API results
- Image compression via Base64
- Efficient re-renders with React hooks
- CSS-based animations
- No unnecessary state updates

## Error Handling

User-friendly error messages for:
- Missing image upload
- API failures
- Network errors
- Invalid file types
- Backend unavailability

## Development

### Development Server
```bash
npm run dev
```
- Hot module reloading
- API proxy to backend (http://localhost:8000)
- Source map support

### ES Lint
```bash
npm run lint
```
Code quality checks with ESLint.

### Environment Setup

Create `.env.local`:
```
VITE_API_URL=http://localhost:8000
```

For different backend URL:
```
VITE_API_URL=https://api.production.com
```

## Build Configuration

### Vite Config
- React plugin for JSX
- Development server proxy
- Fast build times
- Optimized bundle splitting

### Tailwind Config
- Custom medical color palette
- Extended theme
- PostCSS integration
- Autoprefixer for browser compatibility

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS 12+, Android 5+)

## Deployment

### Vercel/Netlify
```bash
npm run build
# Deploy dist folder
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

### Environment for Deployment
Set backend URL in deployment environment:
```
VITE_API_URL=https://your-api-domain.com
```

## Troubleshooting

**Backend connection failed**
- Ensure backend is running: `python main.py`
- Check backend URL in `.env.local`
- Verify CORS is enabled

**Images not loading**
- Check browser console for CORS errors
- Ensure backend API endpoints are correct
- Verify Base64 encoding/decoding

**Styling issues**
- Run: `npm run build` to regenerate CSS
- Clear browser cache
- Check Tailwind configuration

**File upload fails**
- Verify file size < 10MB
- Check file format (PNG/JPG only)
- Ensure backend /predict endpoint is working

## Performance Optimization

- Minimize image sizes before upload
- Use modern browser for better performance
- Enable hardware acceleration in browser
- Consider using WebWorkers for processing

## Future Enhancements

- [ ] Batch image upload and processing
- [ ] 3D volume viewer
- [ ] Model confidence visualization
- [ ] History/previous analysis storage
- [ ] Patient database integration
- [ ] Multi-model selection
- [ ] Real-time processing updates
- [ ] Dark/light theme toggle
- [ ] Export to DICOM format
- [ ] Measurement tools

## Dependencies

### Main
- `react`: UI library
- `react-dom`: DOM rendering

### Build & Development
- `vite`: Build tool
- `@vitejs/plugin-react`: React plugin

### Styling
- `tailwindcss`: CSS framework
- `postcss`: CSS processor
- `autoprefixer`: Browser prefixes

### Icons
- `lucide-react`: Icon library

### API
- `axios`: HTTP client

## License

Part of the Medical Imaging project.

## Support

For issues:
1. Check browser console (F12)
2. Verify backend is running
3. Review API response in Network tab
4. Check `.env.local` configuration
