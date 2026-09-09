# ChatGPT — Style Reference
> graphite ink on warm paper

**Theme:** light

ChatGPT uses a graphite-on-paper language: near-white canvas (#f9f9f9 sidebar) with the main conversation surface staying white, near-black ink for all primary text and icons, and zero chromatic accents. The entire UI is achromatic — meaning is carried by weight (600 headings, 400 body, 500 for emphasis) and spatial rhythm rather than color. Surfaces stay flat; elevation comes from a single hairline border at 1px rgba(0,0,0,0.05) rather than shadow. Controls are small, square-ish (10px radius), and chrome-light so the written response dominates. The system reads as restrained utility software — every pixel earns its place.

## Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Sidebar Mist | `#f9f9f9` | `--color-sidebar-mist` | Sidebar and secondary surface backgrounds — page chrome recedes behind the conversation |
| Pure White | `#ffffff` | `--color-pure-white` | Main canvas and elevated surface — primary reading area, elevated panels, inverted text backgrounds |
| Graphite Ink | `#0d0d0d` | `--color-graphite-ink` | Primary headings, body text, and icon fills on light surfaces. Do not promote it to the primary CTA color |
| Mid Ash | `#5d5d5d` | `--color-mid-ash` | Secondary text and icons — supporting labels, metadata |
| Hollow | `#8f8f8f` | `--color-hollow` | Tertiary text, disabled states, muted helper copy |
| Hairline | `#0000001a` | `--color-hairline` | 1px borders and dividers — rgba black at ~10% opacity, the sole structural separator |
| Hover Veil | `#0000000d` | `--color-hover-veil` | Hover fill on interactive elements |
| Ink Press | `#000000` | `--color-ink-press` | Pressed/inverted surface fill, tooltips, scrim — true black for max contrast moments |
| Deep Charcoal | `#00000080` | `--color-deep-charcoal` | Modal scrim overlay — 50% black behind dialogs and drawers |
| Edge Gray | `#e6e6e6` | `--color-edge-gray` | Stronger divider or inactive surface — used sparingly as a higher-contrast border alternative |

## Tokens — Typography

### System UI font
The entire interface renders in `-apple-system / BlinkMacSystemFont / Segoe UI`, inheriting the OS typeface rather than shipping a custom face.

### Type Scale

| Role | Size | Line Height | Letter Spacing | Token |
|------|------|-------------|----------------|-------|
| caption | 14px | 1.43 | — | `--text-caption` |
| body | 16px | 1.5 | — | `--text-body` |
| heading | 24px | 1.33 | — | `--text-heading` |

## Tokens — Spacing & Shapes

**Density:** compact

### Spacing Scale

| Name | Value | Token |
|------|-------|-------|
| 6 | 6px | `--spacing-6` |
| 8 | 8px | `--spacing-8` |
| 10 | 10px | `--spacing-10` |
| 12 | 12px | `--spacing-12` |
| 16 | 16px | `--spacing-16` |
| 20 | 20px | `--spacing-20` |

### Border Radius

| Element | Value |
|---------|-------|
| nav | 10px |
| cards | 10px |
| links | 16px |
| badges | 0px |
| buttons | 10px |

### Layout

- **Page max-width:** 1200px
- **Section gap:** 24px
- **Card padding:** 16px
- **Element gap:** 6px

## CSS Custom Properties

```css
:root {
  /* Colors */
  --color-sidebar-mist: #f9f9f9;
  --color-pure-white: #ffffff;
  --color-graphite-ink: #0d0d0d;
  --color-mid-ash: #5d5d5d;
  --color-hollow: #8f8f8f;
  --color-hairline: #0000001a;
  --color-hover-veil: #0000000d;
  --color-ink-press: #000000;
  --color-deep-charcoal: #00000080;
  --color-edge-gray: #e6e6e6;

  /* Typography — Font Families */
  --font-apple-system-body: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;

  /* Typography — Scale */
  --text-caption: 14px;
  --leading-caption: 1.43;
  --text-body: 16px;
  --leading-body: 1.5;
  --text-heading: 24px;
  --leading-heading: 1.33;

  /* Typography — Weights */
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;

  /* Spacing */
  --spacing-6: 6px;
  --spacing-8: 8px;
  --spacing-10: 10px;
  --spacing-12: 12px;
  --spacing-16: 16px;
  --spacing-20: 20px;

  /* Layout */
  --page-max-width: 1200px;
  --section-gap: 24px;
  --card-padding: 16px;
  --element-gap: 6px;

  /* Border Radius */
  --radius-lg: 10px;
  --radius-2xl: 16px;
  --radius-nav: 10px;
  --radius-cards: 10px;
  --radius-links: 16px;
  --radius-badges: 0px;
  --radius-buttons: 10px;

  /* Surfaces */
  --surface-sidebar-canvas: #f9f9f9;
  --surface-conversation-canvas: #ffffff;
  --surface-elevated-panel: #ffffff;
}
```

## Quick Color Reference
- text: #0d0d0d (Graphite Ink)
- background: #ffffff (Pure White)
- sidebar background: #f9f9f9 (Sidebar Mist)
- border: #0000001a (Hairline)
- secondary text: #5d5d5d (Mid Ash)
- muted text: #8f8f8f (Hollow)
- primary action: no distinct CTA color

## Surfaces

| Level | Name | Value | Purpose |
|-------|------|-------|---------|
| 0 | Sidebar Canvas | `#f9f9f9` | Left rail background |
| 1 | Conversation Canvas | `#ffffff` | Main reading/writing surface |
| 2 | Elevated Panel | `#ffffff` | Popovers, menus, floating UI |

## Elevation

Elevation is expressed exclusively through 1px hairline borders (#0000001a) on white surfaces, never through drop shadows.
