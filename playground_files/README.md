# Playground Files

Welcome to the playground! This is where you create your PDF templates.

## 📋 Required Files

### `index.html` (Required)
**Your main HTML file - MUST be named `index.html`**

This is the entry point for your PDF. Use Jinja2 syntax to make it dynamic:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>Hello {{ name }}!</h1>
    <p>Date: {{ now.strftime('%Y-%m-%d') }}</p>
</body>
</html>
```

### `params.json` (Required for dynamic content)
**Your data file - MUST be named `params.json`**

All variables you use in your templates must be defined here:

```json
{
  "title": "My PDF Document",
  "name": "John Doe"
}
```

### `styles.css` (Optional but recommended)
Your CSS styles, including print-specific rules:

```css
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: Arial, sans-serif;
}
```

## 🎯 Quick Start Examples

### Example 1: Simple Invoice

**index.html:**
```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>Invoice #{{ invoice_number }}</h1>
    <p>Customer: {{ customer_name }}</p>
    <table>
        {% for item in items %}
        <tr>
            <td>{{ item.name }}</td>
            <td>${{ item.price }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
```

**params.json:**
```json
{
  "invoice_number": "INV-001",
  "customer_name": "ACME Corp",
  "items": [
    {"name": "Widget", "price": 99.99},
    {"name": "Gadget", "price": 149.99}
  ]
}
```

### Example 2: Certificate

**index.html:**
```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="certificate">
        <h1>Certificate of Completion</h1>
        <p>This certifies that</p>
        <h2>{{ student_name }}</h2>
        <p>has successfully completed</p>
        <h3>{{ course_name }}</h3>
        <p>on {{ completion_date }}</p>
    </div>
</body>
</html>
```

**params.json:**
```json
{
  "student_name": "Jane Smith",
  "course_name": "Advanced Python Programming",
  "completion_date": "November 14, 2024"
}
```

## 🔧 Advanced Features

### Template Inheritance

Create reusable layouts using `{% extends %}`:

**base.html:**
```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>Company Name</header>
    {% block content %}{% endblock %}
    <footer>Page {{ now.strftime('%Y') }}</footer>
</body>
</html>
```

**index.html:**
```html
{% extends "base.html" %}

{% block content %}
    <h1>{{ title }}</h1>
    <p>{{ content }}</p>
{% endblock %}
```

### Include Reusable Components

**index.html:**
```html
<!DOCTYPE html>
<html>
<body>
    <h1>{{ title }}</h1>
    {% include "header.html" %}
    {% include "content.html" %}
</body>
</html>
```

## 📁 Organizing Your Files

You can organize CSS and templates in subdirectories:

```
playground_files/
├── index.html           ← REQUIRED: Main entry point
├── params.json          ← REQUIRED: Your data
├── styles.css           ← Main styles
├── base/                ← Subdirectory for base templates
│   ├── layout.html
│   └── common.css
├── components/          ← Reusable components
│   ├── header.html
│   └── footer.html
└── fonts.css            ← Custom fonts
```

## 🌐 Built-in Variables

These variables are always available without defining them in `params.json`:

- `now` - Current datetime object
  - `{{ now.strftime('%Y-%m-%d') }}` - Date
  - `{{ now.strftime('%H:%M') }}` - Time
  - `{{ now.strftime('%B %d, %Y') }}` - Full date

## 💡 Tips

1. **Start Simple** - Begin with a basic `index.html` and `params.json`
2. **Test Incrementally** - Make small changes and watch the PDF update
3. **Use the Preview** - The left panel shows your rendered HTML
4. **Check Console** - Terminal shows generation status and errors
5. **Validate JSON** - Make sure your `params.json` is valid JSON

## 🚀 Workflow

1. Edit `index.html` (your template)
2. Edit `params.json` (your data)
3. Edit `styles.css` (your styles)
4. Save any file
5. Watch the PDF auto-regenerate! ✨

## 📚 Resources

- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [WeasyPrint Documentation](https://weasyprint.org/)
- [CSS for Print Media](https://www.smashingmagazine.com/2015/01/designing-for-print-with-css/)

