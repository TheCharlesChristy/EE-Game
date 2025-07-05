# Multi-Team Gaming System - Style Guide

## Design Philosophy

This styling guide creates a **professional, clean, and engaging** visual experience optimized for large screen viewing in competitive gaming environments. The design emphasizes **clarity, accessibility, and team distinction** while maintaining a cohesive blue-themed aesthetic.

## Core Design Principles

- **Distance Readability**: All text and UI elements sized for comfortable viewing from 10+ feet
- **Professional Clean**: Minimal clutter, clear hierarchy, purposeful use of space
- **Team Distinction**: Each team has unique colors with additional visual markers for accessibility
- **Accessible by Design**: Color-blind friendly through shapes, patterns, and contrast
- **Lighthearted Professional**: Clean and serious but with personality through color accents

---

## Color Palette

### Primary Colors
```css
:root {
  /* Primary Blues */
  --primary-dark-blue: #1a365d;      /* Main backgrounds, headers */
  --primary-medium-blue: #2d5aa0;    /* Interactive elements */
  --primary-light-blue: #4299e1;     /* Accents, highlights */
  
  /* Neutrals */
  --background-white: #ffffff;       /* Main content areas */
  --background-light: #f7fafc;       /* Secondary backgrounds */
  --text-dark: #2d3748;             /* Primary text */
  --text-medium: #4a5568;           /* Secondary text */
  --text-light: #718096;            /* Tertiary text */
  
  /* System Colors */
  --success-green: #38a169;          /* Correct answers, wins */
  --warning-orange: #ed8936;         /* Warnings, time running out */
  --error-red: #e53e3e;             /* Wrong answers, eliminations */
}
```

### Team Colors (8 Teams Maximum)
```css
:root {
  /* Team Colors - Carefully selected for distinction and accessibility */
  --team-1-red: #e53e3e;            /* Red */
  --team-2-orange: #ff8c00;         /* Dark Orange */
  --team-3-yellow: #ffd700;         /* Gold */
  --team-4-green: #38a169;          /* Green */
  --team-5-teal: #319795;           /* Teal */
  --team-6-purple: #805ad5;         /* Purple */
  --team-7-pink: #d53f8c;           /* Pink */
  --team-8-brown: #8b4513;          /* Saddle Brown */
}
```

---

## Typography

### Font Stack
```css
:root {
  --font-primary: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
  --font-monospace: 'SF Mono', 'Monaco', 'Consolas', monospace;
}
```

### Font Sizes (Optimized for Distance Viewing)
```css
:root {
  /* Display Sizes */
  --font-size-display: 4rem;        /* 64px - Game titles, main status */
  --font-size-large: 3rem;          /* 48px - Questions, important info */
  --font-size-medium: 2rem;         /* 32px - Team names, scores */
  --font-size-body: 1.5rem;         /* 24px - General content */
  --font-size-small: 1.25rem;       /* 20px - Details, metadata */
  
  /* Line Heights */
  --line-height-tight: 1.2;
  --line-height-normal: 1.5;
  --line-height-loose: 1.8;
}
```

### Typography Classes
```css
/* Heading Styles */
.text-display {
  font-size: var(--font-size-display);
  font-weight: 700;
  line-height: var(--line-height-tight);
  color: var(--primary-dark-blue);
}

.text-large {
  font-size: var(--font-size-large);
  font-weight: 600;
  line-height: var(--line-height-normal);
  color: var(--text-dark);
}

.text-medium {
  font-size: var(--font-size-medium);
  font-weight: 500;
  line-height: var(--line-height-normal);
  color: var(--text-dark);
}

.text-body {
  font-size: var(--font-size-body);
  font-weight: 400;
  line-height: var(--line-height-normal);
  color: var(--text-medium);
}
```

---

## Layout & Spacing

### Spacing Scale
```css
:root {
  --space-xs: 0.5rem;    /* 8px */
  --space-sm: 1rem;      /* 16px */
  --space-md: 1.5rem;    /* 24px */
  --space-lg: 2rem;      /* 32px */
  --space-xl: 3rem;      /* 48px */
  --space-2xl: 4rem;     /* 64px */
  --space-3xl: 6rem;     /* 96px */
}
```

### Container Styles
```css
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-lg);
}

.full-screen {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.content-area {
  background: var(--background-white);
  border-radius: 12px;
  padding: var(--space-xl);
  box-shadow: 0 4px 20px rgba(26, 54, 93, 0.1);
}
```

---

## Component Styles

### Team Identification System
```css
/* Team Card Base */
.team-card {
  background: var(--background-white);
  border: 3px solid transparent;
  border-radius: 12px;
  padding: var(--space-lg);
  margin: var(--space-sm);
  position: relative;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

/* Team Color Applications */
.team-card[data-team="1"] {
  border-color: var(--team-1-red);
  --team-accent: var(--team-1-red);
}

.team-card[data-team="2"] {
  border-color: var(--team-2-orange);
  --team-accent: var(--team-2-orange);
}

/* Add pattern for accessibility */
.team-card::before {
  content: '';
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  background: var(--team-accent);
  border-radius: 50%;
}

/* Team-specific patterns for accessibility */
.team-card[data-team="1"]::before { border-radius: 50%; }           /* Circle */
.team-card[data-team="2"]::before { border-radius: 0; }             /* Square */
.team-card[data-team="3"]::before { 
  border-radius: 0;
  transform: rotate(45deg);
}                                                                    /* Diamond */
.team-card[data-team="4"]::before { 
  border-radius: 50% 0;
}                                                                    /* Teardrop */
```

### Status Indicators
```css
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: 24px;
  font-weight: 500;
  font-size: var(--font-size-body);
}

.status-active {
  background: rgba(66, 153, 225, 0.1);
  color: var(--primary-medium-blue);
  border: 2px solid var(--primary-light-blue);
}

.status-eliminated {
  background: rgba(229, 62, 62, 0.1);
  color: var(--error-red);
  border: 2px solid var(--error-red);
}

.status-winner {
  background: rgba(56, 161, 105, 0.1);
  color: var(--success-green);
  border: 2px solid var(--success-green);
}
```

### Buttons and Interactive Elements
```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md) var(--space-xl);
  font-size: var(--font-size-body);
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.btn-primary {
  background: var(--primary-medium-blue);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-dark-blue);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(45, 90, 160, 0.3);
}

.btn-secondary {
  background: var(--background-light);
  color: var(--text-dark);
  border: 2px solid var(--primary-light-blue);
}

.btn-large {
  padding: var(--space-lg) var(--space-2xl);
  font-size: var(--font-size-medium);
}
```

---

## Game-Specific Styles

### Reaction Timer Game
```css
.reaction-screen {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-display);
  font-weight: 700;
  transition: background-color 0.1s ease;
}

.reaction-screen.waiting {
  background-color: #dc2626;  /* Red */
  color: white;
}

.reaction-screen.go {
  background-color: #16a34a;  /* Green */
  color: white;
}

.lives-indicator {
  display: flex;
  gap: var(--space-sm);
}

.life-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--success-green);
  border: 2px solid var(--success-green);
}

.life-dot.lost {
  background: transparent;
  border-color: var(--error-red);
}
```

### Wheel Game
```css
.wheel-container {
  width: 400px;
  height: 400px;
  margin: 0 auto;
  position: relative;
}

.wheel-segment {
  position: absolute;
  width: 50%;
  height: 50%;
  transform-origin: 100% 100%;
  border: 3px solid white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: white;
  transition: all 0.3s ease;
}

.wheel-segment.selected {
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
  z-index: 10;
}
```

### Quiz Game
```css
.question-display {
  background: var(--background-white);
  border: 4px solid var(--primary-light-blue);
  border-radius: 16px;
  padding: var(--space-2xl);
  margin: var(--space-xl) 0;
  text-align: center;
  box-shadow: 0 8px 32px rgba(26, 54, 93, 0.15);
}

.buzzer-indicator {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--team-accent);
  color: white;
  padding: var(--space-xl);
  border-radius: 16px;
  font-size: var(--font-size-large);
  font-weight: 700;
  z-index: 1000;
  animation: buzzer-flash 0.5s ease-in-out;
}

@keyframes buzzer-flash {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.1); }
}
```

---

## Animations & Transitions

### Standard Transitions
```css
:root {
  --transition-fast: 0.15s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.5s ease;
}

/* Hover Effects */
.interactive {
  transition: transform var(--transition-fast);
}

.interactive:hover {
  transform: translateY(-2px);
}

/* Loading States */
.loading {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
```

### LED Feedback Simulation
```css
.led-indicator {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #666;
  border: 2px solid #333;
  transition: all 0.2s ease;
}

.led-indicator.active {
  background: var(--team-accent);
  border-color: var(--team-accent);
  box-shadow: 0 0 20px var(--team-accent);
}

.led-indicator.flashing {
  animation: led-flash 0.5s infinite alternate;
}

@keyframes led-flash {
  from { opacity: 1; }
  to { opacity: 0.3; }
}
```

---

## Responsive Design

### Breakpoints
```css
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
}

/* Large screens (default) - optimized for projectors */
@media (min-width: 1024px) {
  .grid-teams {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-lg);
  }
}

/* Medium screens */
@media (max-width: 1023px) {
  .grid-teams {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-md);
  }
  
  :root {
    --font-size-display: 3rem;
    --font-size-large: 2.5rem;
    --font-size-medium: 1.75rem;
  }
}
```

---

## Accessibility Features

### Color Blind Support
```css
/* High contrast mode */
.high-contrast {
  --primary-dark-blue: #000000;
  --background-white: #ffffff;
  --text-dark: #000000;
}

/* Pattern-based team identification */
.team-pattern-1 { background-image: repeating-linear-gradient(45deg, transparent, transparent 4px, rgba(0,0,0,0.1) 4px, rgba(0,0,0,0.1) 8px); }
.team-pattern-2 { background-image: repeating-linear-gradient(90deg, transparent, transparent 4px, rgba(0,0,0,0.1) 4px, rgba(0,0,0,0.1) 8px); }
.team-pattern-3 { background-image: radial-gradient(circle at 50% 50%, transparent 30%, rgba(0,0,0,0.1) 30%); }
```

### Focus States
```css
.focusable:focus {
  outline: 3px solid var(--primary-light-blue);
  outline-offset: 2px;
}

/* Skip links for keyboard navigation */
.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: var(--primary-dark-blue);
  color: white;
  padding: 8px;
  text-decoration: none;
  border-radius: 4px;
}

.skip-link:focus {
  top: 6px;
}
```

---

## Implementation Guidelines

### CSS Organization
```
app/static/css/
├── base.css           # CSS variables, resets, base styles
├── components.css     # Reusable component styles
├── games.css         # Game-specific styles
├── teams.css         # Team identification styles
└── utilities.css     # Utility classes
```

### CSS Loading Order
1. **base.css** - Variables and foundational styles
2. **components.css** - Reusable UI components
3. **teams.css** - Team color and identification
4. **games.css** - Game-specific styling
5. **utilities.css** - Helper classes

### Performance Considerations
- Use CSS custom properties for dynamic theming
- Minimize animations on Raspberry Pi if performance issues arise
- Optimize for hardware acceleration with `transform` and `opacity`
- Use `will-change` property sparingly and only when needed

---

## Usage Examples

### Team Registration Interface
```html
<div class="team-card" data-team="1">
  <div class="team-header">
    <h3 class="text-medium">Team Alpha</h3>
    <div class="led-indicator active"></div>
  </div>
  <div class="team-status">
    <span class="status-indicator status-active">Ready</span>
  </div>
</div>
```

### Game Status Display
```html
<div class="game-status">
  <h1 class="text-display">Reaction Timer</h1>
  <div class="round-info">
    <span class="text-large">Round 3</span>
    <span class="text-body">Time Limit: 180ms</span>
  </div>
</div>
```

This styling guide provides a comprehensive foundation for creating a professional, accessible, and engaging gaming system interface that works well for large screen viewing and team competition scenarios.