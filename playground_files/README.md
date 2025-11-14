# Playground Files

This directory contains all the files you can edit to customize your PDF output.

## 📝 Files

### `index.html`
Your HTML template using Jinja2 syntax.

**Usage:**
- Use `{{ variable }}` to insert values from `params.json`
- Use `{% for item in list %}...{% endfor %}` to loop through arrays
- Use `{% if condition %}...{% endif %}` for conditionals
- Reference `styles.css` for styling

**Example:**
```html
<h1>{{ recipe.name }}</h1>
<p>Batch Size: {{ recipe.batch_size }}x</p>

{% for item in recipe.recipe_items %}
  <div>{{ item.name }}</div>
{% endfor %}
```

### `styles.css`
Your CSS styles that will be applied to the HTML.

**Usage:**
- Define page size and margins using `@page`
- Style all your HTML elements
- Use print-specific CSS properties

**Example:**
```css
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: Arial, sans-serif;
    color: #333;
}
```

### `params.json`
Your data in JSON format that gets injected into the template.

**Usage:**
- Define all your dynamic content here
- Structure your data hierarchically
- Use arrays for lists of items

**Example:**
```json
{
  "recipe": {
    "name": "Classic Marinara Sauce",
    "batch_size": 2,
    "recipe_items": [
      {"name": "Tomatoes", "quantity": "28 oz"}
    ]
  }
}
```

## 🔄 Auto-Regeneration

Any time you save changes to these files, the PDF will automatically regenerate and update in the browser!

## 🌐 Built-in Variables

These variables are always available in your templates:
- `now` - Current datetime
  - `{{ now.strftime('%d/%m/%Y') }}` - Date
  - `{{ now.strftime('%H:%M') }}` - Time

## 💡 Tips

1. **Start Simple** - Begin with a basic template and gradually add complexity
2. **Test Incrementally** - Make small changes and verify the output
3. **Use the Preview** - The left panel shows your rendered HTML, the right shows the PDF
4. **Check the Console** - Terminal logs show generation status and errors

## 📚 Resources

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [WeasyPrint Documentation](https://weasyprint.org/)
- [CSS for Print](https://www.smashingmagazine.com/2015/01/designing-for-print-with-css/)

