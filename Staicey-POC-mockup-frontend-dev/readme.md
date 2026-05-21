# 🚀 Staicey - AI-Powered Travel Assistant

**Staicey** is an intelligent travel planning platform that combines AI chat capabilities with comprehensive hotel search and booking functionality. Built with modern web technologies, it provides users with personalized travel recommendations, real-time hotel information, and an intuitive chat interface for seamless travel planning.

## ✨ Features

### 🤖 AI Chat Interface
- **Intelligent Conversations**: Natural language processing for travel queries
- **Context-Aware Responses**: Remembers conversation history and user preferences
- **Multi-Session Support**: Manage multiple chat sessions with tabs
- **Real-time Messaging**: Instant responses with typing indicators

### 🏨 Hotel Search & Discovery
- **Comprehensive Hotel Data**: Ratings, reviews, amenities, and pricing
- **AI-Generated Insights**: Personalized recommendations and notes
- **Interactive Maps**: Google Maps integration with hotel locations
- **Image Carousel**: Hotel photo galleries with fallback to template images
- **Price Comparison**: Best available rates from multiple sources

### 🎨 Modern User Interface
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Dark/Light Themes**: Customizable appearance with theme switching
- **Smooth Animations**: Framer Motion powered interactions
- **Accessibility**: WCAG compliant components and navigation

### 🔐 User Authentication
- **Secure Login/Registration**: JWT-based authentication system
- **Session Management**: Persistent login states with timeout warnings
- **User Profiles**: Personalized settings and preferences

## 🛠️ Tech Stack

### Frontend Framework
- **Next.js 14**: React-based full-stack framework with App Router
- **TypeScript**: Type-safe development with enhanced IDE support
- **React 18**: Latest React features with concurrent rendering

### UI & Styling
- **Tailwind CSS**: Utility-first CSS framework for rapid development
- **Radix UI**: Accessible, unstyled UI components
- **Lucide React**: Beautiful, customizable icons
- **Framer Motion**: Smooth animations and transitions

### State Management & Data
- **React Context**: Lightweight state management for app-wide data
- **React Hook Form**: Performant forms with validation
- **Zod**: TypeScript-first schema validation

### Maps & External Services
- **Google Maps API**: Interactive maps and location services
- **Embla Carousel**: Touch-friendly image carousels

### Development Tools
- **ESLint**: Code quality and consistency
- **PostCSS**: CSS processing and optimization
- **SWC**: Fast Rust-based JavaScript/TypeScript compiler

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn package manager
- Google Maps API key (for map functionality)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <folder-name>
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Environment Setup**
   Create a `.env.local` file in the root directory:
   ```env
   NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Run the development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Building for Production

```bash
npm run build
npm start
```

## 📁 Project Structure

```
staicey-0813-mvp/
├── app/                          # Next.js App Router
│   ├── chat/                    # Chat functionality
│   │   ├── [id]/               # Dynamic chat sessions
│   │   └── components/         # Chat-specific components
│   ├── context/                # React Context providers
│   ├── globals.css             # Global styles
│   ├── layout.tsx              # Root layout
│   └── page.tsx                # Home page
├── components/                  # Reusable UI components
│   ├── auth/                   # Authentication components
│   ├── custom-components/      # Custom UI components
│   ├── layout/                 # Layout components
│   ├── sections/               # Page sections
│   └── ui/                     # Base UI components
├── hooks/                      # Custom React hooks
├── lib/                        # Utility functions and types
├── public/                     # Static assets
│   └── assets/                # Images, fonts, icons
└── tailwind.config.ts         # Tailwind CSS configuration
```

## 🔧 Key Components

### Chat System
- **ChatWindow**: Main chat interface with message history
- **ChatInput**: User input with suggestion buttons
- **ChatMessage**: Individual message display with hotel results
- **HotelResults**: Hotel search results with interactive carousel

### Authentication
- **UserContext**: Global user state management
- **LoginPopup**: User authentication modal
- **UserNavMenu**: User navigation and settings

### Navigation
- **Sidebar**: Main navigation with chat sessions
- **Header**: Top navigation bar
- **MobileDrawer**: Responsive mobile navigation

## 🎯 Usage Examples

### Starting a Chat
1. Navigate to the chat interface
2. Type your travel query (e.g., "I need a hotel in Sydney for next weekend")
3. Receive AI-generated recommendations and hotel options

### Hotel Search
1. Ask about specific destinations or dates
2. View comprehensive hotel information
3. Compare prices and amenities
4. Access booking links directly

### Managing Sessions
1. Create new chat tabs for different trips
2. Pin important conversations
3. Organize travel planning by destination or purpose

## 🔒 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` | Google Maps API key for map functionality | Yes |
| `NEXT_PUBLIC_API_URL` | Backend API endpoint URL | Yes |

## 🧪 Development

### Code Quality
```bash
npm run lint          # Run ESLint
npm run build         # Build for production
```

### Component Development
- Components are built using TypeScript for type safety
- Follow the established component patterns in the `components/` directory
- Use Tailwind CSS classes for styling
- Implement proper accessibility features

## 📱 Responsive Design

The application is fully responsive and optimized for:
- **Desktop**: Full-featured interface with sidebar navigation
- **Tablet**: Adaptive layout with touch-friendly controls
- **Mobile**: Mobile-first design with drawer navigation

## 🌟 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 🤝 Support

For support and questions:
- Check the existing issues in the repository
- Create a new issue with detailed information
- Contact the development team

---

## **❤️ Staicey.ai ❤️**
