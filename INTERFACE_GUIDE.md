# WeasyPrint Sandbox - Browser Interface

## 🖥️ Visual Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📄 WeasyPrint Live Preview          🟢 Connected   Updated 2s ago   🔄 │
├─────────────────────────────────────────────────────────────────────────┤
│                                     │                                    │
│  🌐 HTML Preview                    │  📑 PDF Output                    │
│  ─────────────────────               │  ──────────────────               │
│                                     │                                    │
│  ┌────────────────────────────┐    │  ┌────────────────────────────┐   │
│  │                            │    │  │                            │   │
│  │  🚀 WeasyPrint Sandbox     │    │  │  🚀 WeasyPrint Sandbox     │   │
│  │                            │    │  │                            │   │
│  │  Live PDF Generation       │    │  │  Live PDF Generation       │   │
│  │  Environment               │    │  │  Environment               │   │
│  │                            │    │  │                            │   │
│  │  Welcome to Your Sandbox!  │    │  │  Welcome to Your Sandbox!  │   │
│  │                            │    │  │                            │   │
│  │  This is a live environment│    │  │  This is a live environment│   │
│  │  where you can edit HTML   │    │  │  where you can edit HTML   │   │
│  │  or CSS and the PDF will   │    │  │  or CSS and the PDF will   │   │
│  │  automatically regenerate. │    │  │  automatically regenerate. │   │
│  │                            │    │  │                            │   │
│  │  How it works:             │    │  │  How it works:             │   │
│  │  1. Edit index.html        │    │  │  1. Edit index.html        │   │
│  │  2. Save the file          │    │  │  2. Save the file          │   │
│  │  3. PDF regenerates auto   │    │  │  3. PDF regenerates auto   │   │
│  │  4. View here!             │    │  │  4. View here!             │   │
│  │                            │    │  │                            │   │
│  │  [... more content ...]    │    │  │  [... PDF page 1 ...]      │   │
│  │                            │    │  │                            │   │
│  └────────────────────────────┘    │  └────────────────────────────┘   │
│                                     │                                    │
│  ← Drag this divider to resize →   │                                    │
│                                     │                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## ✨ Key Features

### Split View Layout

**Left Panel (HTML Preview)**
- Real browser rendering of your HTML
- Includes all CSS styles
- Interactive (if your HTML has JS)
- Scrollable content
- Updates on save

**Right Panel (PDF Output)**
- Embedded PDF viewer
- Shows the exact PDF that WeasyPrint generates
- Auto-scrolls to top on update
- Zoomable
- Downloadable

### Error Display

When PDF generation fails, the right panel transforms:

```
┌─────────────────────────────────────┐
│  ⚠️ PDF Generation Failed           │
├─────────────────────────────────────┤
│                                     │
│  Error Message:                     │
│  ┌─────────────────────────────┐   │
│  │ AttributeError: 'NoneType'  │   │
│  │ object has no attribute 'x' │   │
│  └─────────────────────────────┘   │
│                                     │
│  Full Traceback:                    │
│  ┌─────────────────────────────┐   │
│  │ Traceback (most recent...   │   │
│  │   File "weasyprint.py"...   │   │
│  │   line 42, in generate...   │   │
│  │     result = obj.render()   │   │
│  │ AttributeError: ...         │   │
│  └─────────────────────────────┘   │
│                                     │
│  💡 Tip: Check your HTML and CSS   │
│  syntax. Common issues include:     │
│  unclosed tags, invalid CSS...      │
└─────────────────────────────────────┘
```

### Status Indicator

Top-right corner shows real-time status:

- 🟢 **Green pulsing dot** = Connected and ready
- 🔴 **Red pulsing dot** = Error occurred
- **Timestamp** = Last successful generation
- **File size** = Current PDF size

### Toast Notifications

Bottom-right corner shows temporary notifications:

```
┌─────────────────────────────┐
│ ✓ PDF generated successfully│
└─────────────────────────────┘
```

```
┌─────────────────────────────┐
│ ✗ PDF generation failed!    │
└─────────────────────────────┘
```

## 🔄 Workflow

### Normal Operation

1. **Edit** → Save `index.html` or `styles.css` in your editor
2. **Detect** → File watcher detects the change
3. **Generate** → WeasyPrint generates new PDF
4. **Notify** → WebSocket sends update to browser
5. **Refresh** → Both panels update automatically
6. **Toast** → Success notification appears

### Error Handling

1. **Edit** → Save file with syntax error
2. **Detect** → File watcher detects the change
3. **Attempt** → WeasyPrint tries to generate PDF
4. **Fail** → Exception caught
5. **Display** → Error shown in right panel
6. **Notify** → Error notification appears

### Manual Regeneration

1. **Click** → "🔄 Regenerate" button in header
2. **Force** → Triggers PDF generation
3. **Update** → Panels refresh with new content

## 🎨 Interactive Features

### Resizable Panels

- **Hover** over divider → Cursor changes to ↔
- **Click and drag** → Resize panels
- **Release** → Panels stay at new size
- Resize persists during session

### Auto-Refresh

- **HTML Preview** → Reloads iframe content
- **PDF Output** → Reloads with cache-busting timestamp
- **No page refresh** → Entire page stays loaded
- **WebSocket** → Real-time communication

## 📱 Responsive Behavior

The interface adapts to your screen:

- **Large screens** → 50/50 split by default
- **Medium screens** → Adjustable panels
- **Small screens** → Vertical stacking (mobile)
- **Fullscreen** → Maximizes workspace

## 🎯 Use Cases

### Development Workflow

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Text Editor  │   │   Browser    │   │   Terminal   │
│              │   │              │   │              │
│ Edit HTML/CSS│───│Live Preview  │   │ make logs    │
│              │   │   + PDF      │   │ (optional)   │
└──────────────┘   └──────────────┘   └──────────────┘
     Save              Auto-update         Monitor
```

### Design Iteration

1. Open browser side-by-side with editor
2. Make small CSS changes
3. Save and immediately see results
4. No manual refresh needed
5. Rapid iteration

### Debugging

1. Make change that causes error
2. Error appears in right panel
3. Read full stack trace
4. Fix the issue
5. Save and see success

## 🚀 Getting Started

1. **Run** → `make build && make run`
2. **Browser opens** → http://localhost:5000
3. **Edit** → Open `index.html` in your editor
4. **Save** → Watch the magic happen!
5. **Enjoy** → Live PDF development experience

---

**Pro Tip:** Keep your editor on one monitor, browser on another for the ultimate development experience! 🎉
