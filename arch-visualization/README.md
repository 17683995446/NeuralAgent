# NeuralAgent Architecture Visualization

A beautiful, interactive visualization for exploring the NeuralAgent system architecture.

## 🚀 Quick Start

1. **Start the visualization**

```bash
./start-architecture.sh
```

Or manually:

```bash
cd arch-visualization
npm install
npm run dev
```

The website will be available at: **http://localhost:5173**

## 🌟 Features

### 📊 Pages

1. **** Home** - System overview and quick navigation
2. **Architecture** - Directory structure and 18-layer neural network
3. **Flow** - Data flow visualization
4. **Sequence** - Timeline and sequence diagrams
5. **Monitor** - Real-time file change detection

### 🎨 Design

- Dark theme with glass-morphism UI
- Smooth animations with Framer Motion
- Interactive components
- Responsive design

## 📁 Architecture

```
neural_agent/
├── arch-visualization/
│   ├── src/
│   │   ├── components/
│   │   │   └── Navigation.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Architecture.tsx
│   │   │   ├── Flow.tsx
│   │   │   ├── Sequence.tsx
│   │   │   └── Monitor.tsx
│   │   ├── store/
│   │   │   └── useAppStore.ts
│   │   ├── utils/
│   │   │   └── constants.ts
│   │   └── App.tsx
│   └── package.json
```

## 🛠️ Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Zustand** - State management
- **Lucide React** - Icons

## 📄 License

MIT License - Same as NeuralAgent project
