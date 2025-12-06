# Mental Health Web Application – UI Design System

## 1. Brand Foundations

### Purpose

Provide a calming, trustworthy, low‑cognitive‑load experience that helps users track well‑being, complete exercises, and access supportive resources.

### Design Principles

* Simplicity and clarity
* Emotional safety
* Predictability
* Accessibility first
* Low friction

---

## 2. Color System

### Primary Palette

* **Calm Blue**: #4A90A0
* **Soft Teal**: #70A8A2
* **Muted Indigo**: #6879A1

### Secondary Palette

* **Pale Mint**: #D8EFE8
* **Lavender Gray**: #E3E2F0
* **Warm Neutral**: #F6F4F2

### Support Colors

* **Success**: #6BAF7A
* **Warning**: #E7C45B
* **Critical**: #C46262

### Usage Guidelines

* Large areas: Warm Neutral or Pale Mint
* Highlights and actions: Calm Blue
* Avoid high‑contrast neon or saturated reds

---

## 3. Typography

### Typefaces

* **Primary Font:** Inter (Sans‑serif)

### Scale

* H1: 32px / 1.25
* H2: 24px / 1.3
* H3: 20px / 1.35
* Body Large: 18px / 1.6
* Body: 16px / 1.65
* Caption: 14px / 1.6

### Tone

* Neutral, clear, and non‑judgmental
* Avoid emotional language in UI elements

---

## 4. Spacing & Layout

### Spacing Tokens

* XS: 4px
* S: 8px
* M: 16px
* L: 24px
* XL: 32px
* XXL: 48px

### Layout Rules

* Minimum 16px padding on all container edges
* Generous whitespace to reduce cognitive load
* Max content width: 960px for core flows; 1200px for resource pages

### Grid

* 12‑column responsive grid
* Gutter: 24px on desktop, 16px on mobile

---

## 5. Components

### Buttons

**Primary Button**

* Background: Calm Blue
* Border radius: 8px
* Padding: 12px 20px
* Text: White, Medium weight

**Secondary Button**

* Background: Transparent
* Border: 2px Calm Blue
* Text: Calm Blue

**Tertiary Text Button**

* Understated inline text action

### Inputs

* Rounded corners: 6px
* Background: White
* Border: 1px #D3D6D9
* Focus: 2px Calm Blue outline
* Support states: error text in Critical color

### Cards

* Background: White
* Border radius: 12px
* Shadow: soft, low‑contrast (rgba 0,0,0,0.05)
* Padding: 20px

### Navigation Bar

* Height: 64px
* Background: White
* Sections: Home / Check‑ins / Exercises / Resources / Profile
* Underline indicator on hover/active

### Dialogs

* Max width: 460px
* Background: White
* Border radius: 16px
* Used for journaling prompts, mood check‑ins, and disclaimers

### Tabs

* Soft underline tabs
* Spacing: 16px horizontal
* Active state: Calm Blue underline

---

## 6. Mood Check‑in Components

### Mood Scale Options

* Slider with 5 or 7 points
* Emoji or icon set in muted, non‑bright tones
* Optional open text field

### Journaling Text Box

* Large, calm whitespace
* Optional prompts
* Save locally or encrypted remotely

---

## 7. Exercise Module Components

### Step-by-Step Flow

* Progress indicator at top (dots or line)
* Large text instructions
* Timer when needed (breathing exercises)
* Allow exit or pause at any time

### Breathing Exercise Visual

* Soft pulsing circle
* Slow animation (3–4s transitions)

---

## 8. Resource Library Components

### Resource Card

* Title, short summary, category tag
* Bookmarks icon
* Click opens detailed article

### Category Filters

* Chip-style filters with Calm Blue outline

---

## 9. Accessibility Standards

* WCAG 2.1 AA contrast for all text
* Keyboard navigation on all UI widgets
* Alt text on all icons with functional meaning
* Motion reduction mode (disables animations)
* Scalable up to 200%

---

## 10. Illustrations & Imagery

* Use abstract, soft geometric shapes
* Avoid literal depictions of distress
* Maintain consistent line weight and color palette

---

## 11. Iconography

* Stroke icons, 1.5px–2px weight
* Rounded edges
* Muted tones only
* Categories: mood, exercises, resources, settings

---

## 12. States & Feedback

### Loading

* Soft looping dots or gentle fade animation

### Empty States

* Minimal illustrations
* Clear guidance: "No check‑ins yet. Start with your first one."

### Error States

* Calm, neutral tone
* Example: "Something went wrong. Try again when you're ready."

### Success States

* Very subtle; avoid celebratory bursts

---

## 13. Theme Variants

### Light Theme

* Default; uses warm neutrals and soft pastels

### Dark Theme

* Background: #1F2224
* Surfaces: #2A2E31
* Text: Light Gray
* Primary actions stay Calm Blue with adjusted contrast

---

## 14. Grid-Based Layout Examples

### Home Dashboard

* Header
* Mood check‑in card
* Recommended exercises
* Recent journal entries

### Check‑ins

* Daily mood chart
* History list

### Exercises

* Filter bar
* Card grid

---

## 15. Interaction Patterns (Micro‑UX)

* Never auto‑advance users
* Always allow skipping
* Autosave for journaling
* Provide contextual safety links (static, not intrusive)

---

## 16. Branding Assets

* Logo: simple geometric mark
* Favicon variants
* Print-safe colors (CMYK equivalents)

---

## 17. Development Notes

* Support CSS variables for color tokens
* Use modular scale for typography
* Component library structure: atoms → molecules → organisms → templates

---

End of design system.
